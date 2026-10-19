"""Normaliza la ubicacion de los usuarios con el catalogo geografico del frontend."""

import unicodedata

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from applications.user.models import User


# Version de `@countrystatecity/countries-browser` que usa el frontend. Debe
# coincidir para que los nombres guardados sean los mismos que envia el front.
DEFAULT_CATALOG_VERSION = "2.0.0"
CATALOG_URL = "https://cdn.jsdelivr.net/npm/@countrystatecity/countries-browser@{version}/dist/data/{path}"


def normalize_name(value):
    """Minusculas, sin tildes y con espacios simples para comparar nombres."""

    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.lower().split())


def _names_of(entry, *keys):
    """Nombres normalizados de una entrada del catalogo (nombre, nativo, traducciones)."""

    names = {normalize_name(entry.get(key)) for key in keys}
    names.update(normalize_name(value) for value in (entry.get("translations") or {}).values())
    names.discard("")
    return names


class CountryStateCityCatalog:
    """Lee el catalogo de la libreria desde jsDelivr, igual que el frontend.

    Cada archivo se descarga una sola vez por ejecucion. Un archivo inexistente
    (por ejemplo, ciudades de una provincia sin ciudades) se trata como lista
    vacia.
    """

    def __init__(self, version=DEFAULT_CATALOG_VERSION, timeout=30):
        self.version = version
        self.timeout = timeout
        self._cache = {}

    def load(self, path):
        if path not in self._cache:
            url = CATALOG_URL.format(version=self.version, path=path)
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 404:
                self._cache[path] = None
            else:
                response.raise_for_status()
                self._cache[path] = response.json()
        return self._cache[path]

    def countries(self):
        return self.load("countries.json") or []

    def country_detail(self, iso2):
        return self.load(f"country/{iso2}.json") or {}

    def states(self, iso2):
        return self.load(f"states/{iso2}.json") or []

    def cities(self, country_iso2, state_iso2):
        return self.load(f"cities/{country_iso2}-{state_iso2}.json") or []


class LocationNormalizer:
    """Busca la ubicacion guardada en el catalogo y devuelve sus valores canonicos.

    Los nombres se comparan sin mayusculas ni tildes. El pais se guarda con su
    nombre en espanol (`translations.es`), la provincia y la ciudad con el
    nombre del catalogo, y se completan `province_code` y la provincia cuando
    se deducen de la ciudad. Lo que no se encuentra se conserva tal cual.
    """

    def __init__(self, catalog):
        self.catalog = catalog

    def find_country(self, code, name):
        countries = self.catalog.countries()
        if code:
            for country in countries:
                if (country.get("iso2") or "").upper() == code.upper():
                    return country
        key = normalize_name(name)
        if key:
            for country in countries:
                if key in _names_of(country, "name", "native"):
                    return country
            # Los nombres en espanol solo estan en el detalle de cada pais, que
            # se descarga aparte; se consulta solo si no hubo coincidencia.
            for country in countries:
                detail = self.catalog.country_detail(country["iso2"])
                if key in _names_of(detail, "name", "native"):
                    return country
        return None

    def country_name_es(self, country):
        translations = self.catalog.country_detail(country["iso2"]).get("translations") or {}
        return translations.get("es") or country.get("name") or ""

    def find_state(self, country_iso2, code, name):
        states = self.catalog.states(country_iso2)
        if code:
            for state in states:
                if (state.get("iso2") or "").upper() == code.upper():
                    return state
        key = normalize_name(name)
        if key:
            for state in states:
                if key in _names_of(state, "name", "native"):
                    return state
        return None

    def find_city(self, country_iso2, state, name):
        """Busca la ciudad en su provincia o, si no hay provincia, en todo el pais."""

        key = normalize_name(name)
        if not key:
            return None, None
        states = [state] if state is not None else self.catalog.states(country_iso2)
        for candidate_state in states:
            for city in self.catalog.cities(country_iso2, candidate_state["iso2"]):
                if key in _names_of(city, "name", "native"):
                    return city, candidate_state
        return None, None

    def normalize(self, user):
        """Devuelve `(valores_nuevos, pendientes)` para un usuario."""

        values = {}
        pending = []

        country = self.find_country(user.country_code, user.country_name)
        if country is None:
            pending.append(f"pais '{user.country_name or user.country_code}'")
            return values, pending
        values["country_code"] = country["iso2"]
        values["country_name"] = self.country_name_es(country)

        state = None
        if user.province_code or user.province_name:
            state = self.find_state(country["iso2"], user.province_code, user.province_name)
            if state is None:
                pending.append(f"provincia '{user.province_name or user.province_code}'")

        if user.city_name:
            city, city_state = self.find_city(country["iso2"], state, user.city_name)
            if city is None:
                pending.append(f"ciudad '{user.city_name}'")
            else:
                values["city_name"] = city["name"]
                state = state or city_state

        if state is not None:
            values["province_code"] = state["iso2"]
            values["province_name"] = state["name"]

        changes = {field: value for field, value in values.items() if getattr(user, field) != value}
        return changes, pending


class Command(BaseCommand):
    """Ajusta pais, provincia y ciudad de los usuarios al catalogo del frontend.

    Pensado para correrse una vez despues de `user.0006_user_location_text`,
    que copia la ubicacion de los catalogos antiguos con sus nombres
    historicos. La universidad no se toca porque es texto libre.
    """

    help = (
        "Normalize User country/province/city text fields against the "
        "@countrystatecity/countries-browser catalog used by the frontend."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report the changes that would be applied.",
        )
        parser.add_argument(
            "--catalog-version",
            default=DEFAULT_CATALOG_VERSION,
            help=f"Version of the catalog package (default {DEFAULT_CATALOG_VERSION}); must match the frontend.",
        )

    def get_catalog(self, version):
        return CountryStateCityCatalog(version=version)

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        normalizer = LocationNormalizer(self.get_catalog(options["catalog_version"]))

        users = User.objects.filter(
            ~Q(country_code="") | ~Q(country_name="") | ~Q(province_name="") | ~Q(city_name="")
        ).order_by("pk")

        updated = 0
        pending_users = []
        try:
            for user in users.iterator():
                changes, pending = normalizer.normalize(user)
                if changes:
                    summary = ", ".join(
                        f"{field}: '{getattr(user, field)}' -> '{value}'" for field, value in changes.items()
                    )
                    self.stdout.write(f"[{user.pk}] {user.email}: {summary}")
                    if not dry_run:
                        User.objects.filter(pk=user.pk).update(**changes)
                    updated += 1
                if pending:
                    pending_users.append((user, pending))
        except requests.RequestException as exc:
            raise CommandError(f"No se pudo descargar el catalogo geografico: {exc}") from exc

        action = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} {updated} user location(s)."))

        if pending_users:
            self.stdout.write(self.style.WARNING(
                f"{len(pending_users)} user(s) with values not found in the catalog (kept as they are):"
            ))
            for user, pending in pending_users:
                self.stdout.write(f"  [{user.pk}] {user.email}: {', '.join(pending)}")
