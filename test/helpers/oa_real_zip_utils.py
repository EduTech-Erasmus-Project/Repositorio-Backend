"""Helpers reutilizables para pruebas que suben un OA ZIP real.

Este módulo concentra la lógica común que varias suites usan para:
- localizar el ZIP real de prueba
- envolverlo como `SimpleUploadedFile`
- parsear la metadata que devuelve el endpoint de upload
- transformar esa metadata al payload completo esperado por el endpoint de
  metadata

La idea es evitar que cada suite repita el mismo mapeo largo y, al mismo
tiempo, dejar documentado que estructura de upload se considera valida.
"""

import json
import os
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile


def get_real_zip_path():
    """Resuelve la ruta del ZIP real usada por las pruebas de upload.

    Primero intenta `TEST_REAL_OA_ZIP_PATH` para permitir overrides locales.
    Si no existe, usa el fixture versionado dentro del repositorio.
    """
    repository_root = Path(__file__).resolve().parents[2]
    default_zip_path = repository_root / "test" / "fixtures" / "oa_real_test.zip"
    provided_zip_path = os.getenv("TEST_REAL_OA_ZIP_PATH")
    return Path(provided_zip_path) if provided_zip_path else default_zip_path


def build_real_zip_upload_file():
    """Construye un `SimpleUploadedFile` listo para enviar el ZIP real al endpoint."""
    zip_path = get_real_zip_path()
    if not zip_path.exists():
        raise FileNotFoundError(
            "No existe el ZIP de prueba real. "
            "Define TEST_REAL_OA_ZIP_PATH o coloca el archivo en "
            f"{zip_path}."
        )
    return SimpleUploadedFile(
        zip_path.name,
        zip_path.read_bytes(),
        content_type="application/zip",
    )


def _pick(data, *path):
    """Obtiene un valor anidado siguiendo una ruta de claves.

    Si falta algún nivel, devuelve `None` en vez de lanzar excepción. Esto
    permite mapear metadata parcial sin llenar el helper principal de `try`.
    """
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _flatten_strings(value):
    """Normaliza valores mixtos a una lista plana de strings limpios.

    El metadata parser legacy puede devolver strings, listas, dicts o valores
    simples. Este helper unifica todo a una sola forma consumible.
    """
    if value is None:
        return []
    if isinstance(value, str):
        clean = value.strip()
        return [clean] if clean else []
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_flatten_strings(item))
        return items
    if isinstance(value, dict):
        items = []
        for item in value.values():
            items.extend(_flatten_strings(item))
        return items
    clean = str(value).strip()
    return [clean] if clean else []


def _first_string(value, default=""):
    """Retorna el primer string útil de un valor ya normalizado."""
    values = _flatten_strings(value)
    return values[0] if values else default


def _join_strings(value):
    """Une strings normalizados, elimina duplicados y los separa por coma."""
    values = _flatten_strings(value)
    if not values:
        return ""
    deduplicated = []
    for item in values:
        if item not in deduplicated:
            deduplicated.append(item)
    return ", ".join(deduplicated)


def parse_upload_metadata(upload_response_data):
    """Extrae `metadata` desde la respuesta del upload en formato uniforme.

    El endpoint historicamente puede devolver `metadata` como string JSON o
    como dict ya parseado. Este helper absorbe esa diferencia.
    """
    metadata_raw = upload_response_data.get("metadata")
    if isinstance(metadata_raw, str):
        return json.loads(metadata_raw)
    if isinstance(metadata_raw, dict):
        return metadata_raw
    raise ValueError("El campo metadata del upload no tiene formato esperado.")


def build_metadata_payload_from_upload(
    upload_response_data,
    education_level_id,
    knowledge_area_id,
    license_id,
    avatar_file,
):
    """Mapea la metadata extraída del ZIP al payload completo de alta de metadata.

    Este helper traduce la salida del upload real al shape exacto que espera
    el endpoint `/learning-object-metadata/`. El objetivo no es validar cada
    campo del parser, sino construir un payload realista y repetible para las
    suites que prueban el flujo completo.
    """
    metadata = parse_upload_metadata(upload_response_data)
    # El flag de adaptación sale del análisis que hizo el endpoint de upload.
    adapted_flag = (
        upload_response_data.get("tag_count", {}).get("is_adapted_oer", False) is True
    )

    # Este payload replica el shape real esperado por el endpoint de metadata.
    payload = {
        "learning_object_file": upload_response_data["oa_file"]["id"],
        "adaptation": "adapted" if adapted_flag else "none",
        "avatar": avatar_file,
        "education_levels": education_level_id,
        "knowledge_area": knowledge_area_id,
        "license": license_id,
        "general_catalog": _join_strings(_pick(metadata, "general", "identifier", "catalog")),
        "general_entry": _join_strings(_pick(metadata, "general", "identifier", "entry")),
        "general_title": _first_string(_pick(metadata, "general", "title", "title")),
        "general_language": _first_string(
            _pick(metadata, "general", "language", "language"), default="es"
        ),
        "general_description": _join_strings(
            _pick(metadata, "general", "description", "description")
        ),
        "general_keyword": _join_strings(_pick(metadata, "general", "keyword", "keyword")),
        "general_coverage": _join_strings(
            _pick(metadata, "general", "coverage", "coverage")
        ),
        "general_structure": _join_strings(_pick(metadata, "general", "structure", "value")),
        "general_aggregation_Level": _join_strings(
            _pick(metadata, "general", "aggregationLevel", "value")
        ),
        "life_cycle_version": _join_strings(_pick(metadata, "lifeCycle", "version", "version")),
        "life_cycle_status": _join_strings(_pick(metadata, "lifeCycle", "status", "value")),
        "life_cycle_role": _join_strings(_pick(metadata, "lifeCycle", "contribute", "role")),
        "life_cycle_entity": _join_strings(_pick(metadata, "lifeCycle", "contribute", "entity")),
        "life_cycle_dateTime": _join_strings(
            _pick(metadata, "lifeCycle", "contribute", "date", "dateTime")
        ),
        "life_cycle_description": _join_strings(
            _pick(metadata, "lifeCycle", "contribute", "date", "description")
        ),
        "meta_metadata_catalog": _join_strings(
            _pick(metadata, "metaMetadata", "identifier", "catalog")
        ),
        "meta_metadata_entry": _join_strings(
            _pick(metadata, "metaMetadata", "identifier", "entry")
        ),
        "meta_metadata_role": _join_strings(
            _pick(metadata, "metaMetadata", "contribute", "role")
        ),
        "meta_metadata_entity": _join_strings(
            _pick(metadata, "metaMetadata", "contribute", "entity")
        ),
        "meta_metadata_dateTime": _join_strings(
            _pick(metadata, "metaMetadata", "contribute", "date", "dateTime")
        ),
        "meta_metadata_description": _join_strings(
            _pick(metadata, "metaMetadata", "contribute", "date", "description")
        ),
        "technical_format": _join_strings(_pick(metadata, "technical", "format", "format")),
        "technical_size": _join_strings(_pick(metadata, "technical", "size", "size")),
        "technical_location": _join_strings(
            _pick(metadata, "technical", "location", "location")
        ),
        "technical_requirement_type": _join_strings(
            _pick(metadata, "technical", "requirement", "type")
        ),
        "technical_requirement_name": _join_strings(
            _pick(metadata, "technical", "requirement", "name")
        ),
        "technical_requirement_minimumVersion": _join_strings(
            _pick(metadata, "technical", "requirement", "minimumVersion")
        ),
        "technical_installationRremarks": _join_strings(
            _pick(metadata, "technical", "installationRemarks", "installationRemarks")
        ),
        "technical_otherPlatformRequirements": _join_strings(
            _pick(
                metadata,
                "technical",
                "otherPlatformRequirements",
                "otherPlatformRequirements",
            )
        ),
        "technical_dateTime": _join_strings(_pick(metadata, "technical", "duration", "duration")),
        "technical_description": _join_strings(
            _pick(metadata, "technical", "description", "description")
        ),
        "educational_interactivityType": _join_strings(
            _pick(metadata, "educational", "interactivityType", "value")
        ),
        "educational_learningResourceType": _join_strings(
            _pick(metadata, "educational", "learningResourceType", "value")
        ),
        "educational_interactivityLevel": _join_strings(
            _pick(metadata, "educational", "interactivityLevel", "value")
        ),
        "educational_semanticDensity": _join_strings(
            _pick(metadata, "educational", "semanticDensity", "value")
        ),
        "educational_intendedEndUserRole": _join_strings(
            _pick(metadata, "educational", "intendedEndUserRole", "value")
        ),
        "educational_context": _join_strings(
            _pick(metadata, "educational", "context", "value")
        ),
        "educational_typicalAgeRange": _join_strings(
            _pick(metadata, "educational", "typicalAgeRange", "typicalAgeRange")
        ),
        "educational_difficulty": _join_strings(
            _pick(metadata, "educational", "difficulty", "value")
        ),
        "educational_typicalLearningTime_dateTime": _join_strings(
            _pick(metadata, "educational", "typicalLearningTime", "duration")
        ),
        "educational_typicalLearningTime_description": _join_strings(
            _pick(metadata, "educational", "typicalLearningTime", "description")
        ),
        "educational_description": _join_strings(
            _pick(metadata, "educational", "description", "description")
        ),
        "educational_language": _join_strings(
            _pick(metadata, "educational", "language", "language")
        ),
        "rights_cost": _join_strings(_pick(metadata, "rights", "cost", "value")),
        "rights_copyrightAndOtherRestrictions": _join_strings(
            _pick(metadata, "rights", "copyrightAndOtherRestrictions", "value")
        ),
        "rights_description": _join_strings(
            _pick(metadata, "rights", "description", "description")
        ),
        "relation_kind": _join_strings(_pick(metadata, "relation", "kind", "value")),
        "relation_catalog": _join_strings(
            _pick(metadata, "relation", "resource", "identifier", "catalog")
        ),
        "relation_entry": _join_strings(
            _pick(metadata, "relation", "resource", "identifier", "entry")
        ),
        "relation_description": _join_strings(
            _pick(metadata, "relation", "resource", "description", "description")
        ),
        "annotation_entity": _join_strings(_pick(metadata, "annotation", "entity", "entity")),
        "annotation_date_dateTime": _join_strings(
            _pick(metadata, "annotation", "date", "dateTime")
        ),
        "annotation_date_description": _join_strings(
            _pick(metadata, "annotation", "date", "description")
        ),
        "annotation_description": _join_strings(
            _pick(metadata, "annotation", "description", "description")
        ),
        "annotation_modeaccess": _join_strings(
            _pick(metadata, "annotation", "modeaccess", "value")
        ),
        "annotation_modeaccesssufficient": _join_strings(
            _pick(metadata, "annotation", "modeaccesssufficient", "value")
        ),
        "annotation_rol": _join_strings(_pick(metadata, "annotation", "Rol", "value")),
        "classification_purpose": _join_strings(
            _pick(metadata, "classification", "purpose", "value")
        ),
        "classification_taxonPath_source": _join_strings(
            _pick(metadata, "classification", "taxonPath", "source", "source")
        ),
        "classification_taxonPath_taxon": _join_strings(
            _pick(metadata, "classification", "taxonPath", "taxon", "taxon")
        ),
        "classification_description": _join_strings(
            _pick(metadata, "classification", "description", "description")
        ),
        "classification_keyword": _join_strings(
            _pick(metadata, "classification", "keyword", "keyword")
        ),
        "accesibility_summary": _join_strings(
            _pick(metadata, "accesibility", "description", "description")
        ),
        "accesibility_features": _join_strings(
            _pick(metadata, "accesibility", "accessibilityfeatures", "resourcecontent")
        ),
        "accesibility_hazard": _join_strings(
            _pick(metadata, "accesibility", "accessibilityhazard", "properties")
        ),
        "accesibility_control": _join_strings(
            _pick(metadata, "accesibility", "accessibilitycontrol", "methods")
        ),
        "accesibility_api": _join_strings(
            _pick(metadata, "accesibility", "accessibilityAPI", "compatibleresource")
        ),
    }

    # Sin título general no se puede registrar correctamente el OA.
    if not payload["general_title"]:
        raise ValueError(
            "No se pudo extraer 'general_title' desde metadata real del ZIP."
        )

    return payload
