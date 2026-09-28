"""Pruebas funcionales completas del módulo `address`.

Este archivo valida el contrato principal de los catálogos geográfico-
académicos del sistema:
- CRUD básico de cada recurso
- forma general de las respuestas
- filtros de activos
- filtros derivados por país, ciudad o universidad

La idea no es probar permisos complejos, sino comprobar que los endpoints
públicos y administrativos del módulo conservan el comportamiento esperado.
"""

from django.test import TestCase
from rest_framework.test import APIClient

from applications.address.models import Campus, City, Country, Province, University


class AddressFullFlowTests(TestCase):
    """Cubre el flujo principal de los recursos expuestos por `address`."""

    def setUp(self):
        """Construye una jerarquía mínima con registros activos e inactivos.

        La fixture deja un árbol geográfico completo:
        país -> provincia -> ciudad -> universidad -> campus

        En cada nivel se crea al menos un elemento activo y uno inactivo para
        poder verificar filtros como `active` y evitar falsos positivos.
        """
        self.client = APIClient()

        # Paises base para filtros globales y relaciones posteriores.
        self.country_ec = Country.objects.create(name="Ecuador", is_active=True)
        self.country_us = Country.objects.create(name="USA", is_active=False)

        # Provincias enlazadas a cada pais.
        self.province_pichincha = Province.objects.create(
            name="Pichincha",
            is_active=True,
            country=self.country_ec,
        )
        self.province_texas = Province.objects.create(
            name="Texas",
            is_active=False,
            country=self.country_us,
        )

        # Ciudades enlazadas a cada provincia.
        self.city_quito = City.objects.create(
            name="Quito",
            is_active=True,
            province=self.province_pichincha,
        )
        self.city_houston = City.objects.create(
            name="Houston",
            is_active=False,
            province=self.province_texas,
        )

        # Universidades por pais para probar filtros directos y derivados.
        self.university_ups = University.objects.create(
            name="UPS",
            is_active=True,
            country=self.country_ec,
        )
        self.university_ut = University.objects.create(
            name="UT",
            is_active=False,
            country=self.country_us,
        )

        # Campus por universidad y ciudad para validar relaciones anidadas.
        self.campus_sur = Campus.objects.create(
            name="Campus Sur",
            address="Av. Sur",
            is_active=True,
            university=self.university_ups,
            city=self.city_quito,
        )
        self.campus_north = Campus.objects.create(
            name="Campus North",
            address="North Ave",
            is_active=False,
            university=self.university_ut,
            city=self.city_houston,
        )

    def test_country_crud_and_active_endpoint(self):
        """Valida el contrato completo de `Country` y su listado de activos.

        Verifica que:
        - el listado inicial devuelve los dos países base
        - se puede crear un país nuevo
        - el detalle por id devuelve el recurso creado
        - el update cambia nombre y `is_active`
        - `/countries/active` solo expone países activos
        - el delete elimina el registro del catalogo
        """
        list_response = self.client.get("/api/v1/address/countries/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)

        create_response = self.client.post(
            "/api/v1/address/countries/",
            {"name": "Colombia", "is_active": True},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        country_id = create_response.data["id"]

        retrieve_response = self.client.get(f"/api/v1/address/countries/{country_id}")
        self.assertEqual(retrieve_response.status_code, 200, retrieve_response.data)
        self.assertEqual(retrieve_response.data["name"], "Colombia")

        update_response = self.client.put(
            f"/api/v1/address/countries/{country_id}",
            {"name": "Colombia Actualizada", "is_active": False},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        updated_country = Country.objects.get(id=country_id)
        self.assertEqual(updated_country.name, "Colombia Actualizada")
        self.assertFalse(updated_country.is_active)

        active_response = self.client.get("/api/v1/address/countries/active")
        self.assertEqual(active_response.status_code, 200, active_response.data)
        active_ids = [country["id"] for country in active_response.data]
        self.assertIn(self.country_ec.id, active_ids)
        self.assertNotIn(self.country_us.id, active_ids)
        self.assertNotIn(country_id, active_ids)

        delete_response = self.client.delete(f"/api/v1/address/countries/{country_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Country.objects.filter(id=country_id).exists())

    def test_province_crud_list_and_filter_by_country(self):
        """Valida CRUD de provincias y el filtro manual por país.

        Además de create/update/delete, esta prueba comprueba que:
        - el `list` incluye la relación anidada con `country`
        - `/province/country/<id>` solo devuelve provincias del país pedido
        - provincias de otros países quedan fuera del resultado
        """
        list_response = self.client.get("/api/v1/address/province/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(list_response.data[0]["country"]["id"], self.country_ec.id)

        create_response = self.client.post(
            "/api/v1/address/province/",
            {"name": "Azuay", "is_active": True, "country": self.country_ec.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        province_id = create_response.data["id"]

        by_country_response = self.client.get(f"/api/v1/address/province/country/{self.country_ec.id}")
        self.assertEqual(by_country_response.status_code, 200, by_country_response.data)
        returned_ids = [province["id"] for province in by_country_response.data]
        self.assertIn(self.province_pichincha.id, returned_ids)
        self.assertIn(province_id, returned_ids)
        self.assertNotIn(self.province_texas.id, returned_ids)

        update_response = self.client.put(
            f"/api/v1/address/province/{province_id}",
            {"name": "Azuay Actualizada", "is_active": False, "country": self.country_ec.id},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        updated_province = Province.objects.get(id=province_id)
        self.assertEqual(updated_province.name, "Azuay Actualizada")
        self.assertFalse(updated_province.is_active)

        delete_response = self.client.delete(f"/api/v1/address/province/{province_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Province.objects.filter(id=province_id).exists())

    def test_city_crud_list_and_active_endpoint(self):
        """Valida CRUD de ciudades y el endpoint de ciudades activas.

        La prueba asegura que el listado expone la provincia relacionada y que
        `/cities/active` respeta correctamente el flag `is_active`.
        """
        list_response = self.client.get("/api/v1/address/city/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(list_response.data[0]["province"]["id"], self.province_pichincha.id)

        create_response = self.client.post(
            "/api/v1/address/city/",
            {"name": "Cuenca", "is_active": True, "province": self.province_pichincha.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        city_id = create_response.data["id"]

        update_response = self.client.put(
            f"/api/v1/address/city/{city_id}",
            {"name": "Cuenca Actualizada", "is_active": False, "province": self.province_pichincha.id},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        updated_city = City.objects.get(id=city_id)
        self.assertEqual(updated_city.name, "Cuenca Actualizada")
        self.assertFalse(updated_city.is_active)

        active_response = self.client.get("/api/v1/address/cities/active")
        self.assertEqual(active_response.status_code, 200, active_response.data)
        active_ids = [city["id"] for city in active_response.data]
        self.assertIn(self.city_quito.id, active_ids)
        self.assertNotIn(self.city_houston.id, active_ids)
        self.assertNotIn(city_id, active_ids)

        delete_response = self.client.delete(f"/api/v1/address/city/{city_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(City.objects.filter(id=city_id).exists())

    def test_university_crud_and_filters(self):
        """Valida CRUD de universidades y sus filtros públicos derivados.

        En particular comprueba tres cosas importantes del módulo:
        - `/universities/active` filtra por `is_active`
        - `/universities/active/<country>` restringe por país activo
        - `/universities-by-city/<city>` devuelve universidades del país al
          que pertenece la ciudad, no solo campus de esa ciudad
        """
        list_response = self.client.get("/api/v1/address/university/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(list_response.data[0]["country"]["id"], self.country_ec.id)

        create_response = self.client.post(
            "/api/v1/address/university/",
            {"name": "UCE", "is_active": True, "country": self.country_ec.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        university_id = create_response.data["id"]

        active_response = self.client.get("/api/v1/address/universities/active")
        self.assertEqual(active_response.status_code, 200, active_response.data)
        active_ids = [uni["id"] for uni in active_response.data]
        self.assertIn(self.university_ups.id, active_ids)
        self.assertIn(university_id, active_ids)
        self.assertNotIn(self.university_ut.id, active_ids)

        by_country_response = self.client.get(f"/api/v1/address/universities/active/{self.country_ec.id}")
        self.assertEqual(by_country_response.status_code, 200, by_country_response.data)
        by_country_ids = [uni["id"] for uni in by_country_response.data]
        self.assertIn(self.university_ups.id, by_country_ids)
        self.assertIn(university_id, by_country_ids)
        self.assertNotIn(self.university_ut.id, by_country_ids)

        by_city_response = self.client.get(f"/api/v1/address/universities-by-city/{self.city_quito.id}")
        self.assertEqual(by_city_response.status_code, 200, by_city_response.data)
        by_city_ids = [uni["id"] for uni in by_city_response.data]
        self.assertIn(self.university_ups.id, by_city_ids)
        self.assertIn(university_id, by_city_ids)
        self.assertNotIn(self.university_ut.id, by_city_ids)

        update_response = self.client.put(
            f"/api/v1/address/university/{university_id}",
            {"name": "UCE Actualizada", "is_active": False, "country": self.country_ec.id},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        updated_university = University.objects.get(id=university_id)
        self.assertEqual(updated_university.name, "UCE Actualizada")
        self.assertFalse(updated_university.is_active)

        delete_response = self.client.delete(f"/api/v1/address/university/{university_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(University.objects.filter(id=university_id).exists())

    def test_campus_crud_and_active_filters(self):
        """Valida CRUD de campus y filtros de activos por universidad.

        también comprueba que el `list` expone anidadas las relaciones con
        universidad y ciudad, que son parte importante del contrato de lectura
        enriquecida del módulo.
        """
        list_response = self.client.get("/api/v1/address/campus/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 2)
        self.assertEqual(list_response.data[0]["university"]["id"], self.university_ups.id)
        self.assertEqual(list_response.data[0]["city"]["id"], self.city_quito.id)

        create_response = self.client.post(
            "/api/v1/address/campus/",
            {
                "name": "Campus Centro",
                "address": "Av. Centro",
                "is_active": True,
                "university": self.university_ups.id,
                "city": self.city_quito.id,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        campus_id = create_response.data["id"]

        active_response = self.client.get("/api/v1/address/campus/active")
        self.assertEqual(active_response.status_code, 200, active_response.data)
        active_ids = [campus["id"] for campus in active_response.data]
        self.assertIn(self.campus_sur.id, active_ids)
        self.assertIn(campus_id, active_ids)
        self.assertNotIn(self.campus_north.id, active_ids)

        by_university_response = self.client.get(f"/api/v1/address/campus/active/{self.university_ups.id}")
        self.assertEqual(by_university_response.status_code, 200, by_university_response.data)
        by_university_ids = [campus["id"] for campus in by_university_response.data]
        self.assertIn(self.campus_sur.id, by_university_ids)
        self.assertIn(campus_id, by_university_ids)
        self.assertNotIn(self.campus_north.id, by_university_ids)

        update_response = self.client.put(
            f"/api/v1/address/campus/{campus_id}",
            {
                "name": "Campus Centro Actualizado",
                "address": "Av. Centro Nueva",
                "is_active": False,
                "university": self.university_ups.id,
                "city": self.city_quito.id,
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        updated_campus = Campus.objects.get(id=campus_id)
        self.assertEqual(updated_campus.name, "Campus Centro Actualizado")
        self.assertFalse(updated_campus.is_active)

        delete_response = self.client.delete(f"/api/v1/address/campus/{campus_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Campus.objects.filter(id=campus_id).exists())
