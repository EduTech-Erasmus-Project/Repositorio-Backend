"""Pruebas de filtros y listados públicos de objetos de aprendizaje.

Esta suite cubre el buscador publico principal y endpoints relacionados que
solo deben exponer OAs publicados. El foco está en cuatro grupos de casos:
- el buscador base no debe incluir OAs privados
- los filtros por texto, catálogos y accesibilidad deben combinarse bien
- algunos aliases legacy del frontend deben seguir funcionando
- listados derivados como `populars` o `learning-objects-most-recent` deben
  respetar la misma exclusión de contenido privado

Estas pruebas existen para proteger regresiones visibles en pantallas publicas
y también en consultas autenticadas que reutilizan el mismo buscador.
"""

import io
import shutil
from datetime import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from roabackend.settings import DOMAIN
from applications.education_level.models import EducationLevel
from applications.evaluation_collaborating_expert.models import EvaluationCollaboratingExpert
from applications.interaction.models import Interaction
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from applications.user.models import CollaboratingExpert, Teacher
from test.helpers.temp_media_root import build_test_media_root


class PublicOAFilterTests(TestCase):
    """Verifica el comportamiento del buscador público y rankings derivados."""

    def setUp(self):
        """Prepara una colección pequeña pero variada de OAs para filtrar.

        La fixture crea un docente propietario, un experto colaborador, varios
        catálogos y cinco OAs: cuatro públicos con atributos distintos y uno
        privado que sirve como control negativo en todos los listados.
        """
        self.media_root = build_test_media_root("test-media-oa-filter-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

        self.user_model = get_user_model()
        self.teacher_user = self._create_teacher_user()
        self.expert_user = self._create_expert_user()
        self._sequence = 0

        self.level_1 = EducationLevel.objects.create(name_es="Primaria OA", name_en="Primary OA")
        self.level_2 = EducationLevel.objects.create(name_es="Secundaria OA", name_en="Secondary OA")

        self.area_1 = KnowledgeArea.objects.create(
            name_es="Programación",
            description_es="Desc",
            name_en="Programming",
            description_en="Desc",
        )
        self.area_2 = KnowledgeArea.objects.create(
            name_es="Electrónica",
            description_es="Desc",
            name_en="Electronics",
            description_en="Desc",
        )

        self.license_1 = License.objects.create(
            name_es="Creative Commons OA",
            name_en="Creative Commons OA",
            value="CC-OA",
        )
        self.license_2 = License.objects.create(
            name_es="GPL OA",
            name_en="GPL OA",
            value="GPL-OA",
        )

        # OAs públicos usados por el buscador y los rankings.
        self.oa_python = self._create_learning_object_metadata(
            title="Curso Python Básico",
            description="Introducción práctica a programación",
            education_level=self.level_1,
            knowledge_area=self.area_1,
            license_obj=self.license_1,
            public=True,
            accesibility_features="captions",
            accesibility_hazard="noFlashingHazard",
            accesibility_control="fullkeyboardcontrol",
            annotation_modeaccess="Visual",
        )
        self.oa_robotica = self._create_learning_object_metadata(
            title="Robótica Educativa",
            description="Incluye ejemplos con audioDescription",
            education_level=self.level_2,
            knowledge_area=self.area_2,
            license_obj=self.license_2,
            public=True,
            accesibility_features="audioDescription",
            accesibility_hazard="FlashingHazard",
            accesibility_control="fullMouseControl",
            annotation_modeaccess="Auditory",
        )
        self.oa_python_avanzado = self._create_learning_object_metadata(
            title="Taller Avanzado",
            description="Python para análisis de datos",
            education_level=self.level_1,
            knowledge_area=self.area_1,
            license_obj=self.license_1,
            public=True,
            accesibility_features="ttsMarkup",
            accesibility_hazard="nomotionsimulationHazard",
            accesibility_control="fullkeyboardcontrol",
            annotation_modeaccess="Text",
        )
        self.oa_color_dependent = self._create_learning_object_metadata(
            title="Curso Accesible por Color",
            description="Incluye contenido dependiente del color",
            education_level=self.level_2,
            knowledge_area=self.area_2,
            license_obj=self.license_2,
            public=True,
            accesibility_features="alternativeText",
            accesibility_hazard="noFlashingHazard",
            accesibility_control="fullMouseControl",
            annotation_modeaccess="colorDependent",
        )

        # OA privado de control: no debe salir en endpoints públicos.
        self.oa_privado = self._create_learning_object_metadata(
            title="Python Privado",
            description="No debe aparecer en búsqueda pública",
            education_level=self.level_1,
            knowledge_area=self.area_1,
            license_obj=self.license_1,
            public=False,
            accesibility_features="captions",
            accesibility_hazard="noFlashingHazard",
            accesibility_control="fullkeyboardcontrol",
            annotation_modeaccess="Visual",
        )

    def tearDown(self):
        """Restaura MEDIA_ROOT y borra archivos temporales."""
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_teacher_user(self):
        """Crea docente propietario de OAs en los datos de prueba."""
        teacher = Teacher.objects.create(is_active=True, is_account_active=True)
        user = self.user_model.objects.create_general_user(
            email="teacher-oa-filter@example.com",
            first_name="Teacher",
            last_name="OAFilter",
            password="StrongPass123",
        )
        user.teacher = teacher
        user.save()
        return user

    def _create_expert_user(self):
        """Crea un experto colaborador para cubrir is_evaluated en búsquedas."""
        expert = CollaboratingExpert.objects.create(
            expert_level="Alto",
            is_active=True,
            is_account_active=True,
        )
        user = self.user_model.objects.create_general_user(
            email="expert-oa-filter@example.com",
            first_name="Expert",
            last_name="OAFilter",
            password="StrongPass123",
        )
        user.collaboratingExpert = expert
        user.save()
        return user

    def _build_avatar_png(self):
        """Genera una imagen válida para el campo avatar."""
        image_bytes = io.BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        return SimpleUploadedFile(
            "avatar-oa-filter.png",
            image_bytes.read(),
            content_type="image/png",
        )

    def _create_learning_object_file(self, seq):
        """Crea un LearningObjectFile mínimo para asociar metadata."""
        return LearningObjectFile.objects.create(
            file=SimpleUploadedFile(f"oa-filter-{seq}.zip", b"PK\x03\x04"),
            url=f"http://testserver/media/catalog/oa-filter-{seq}/index.html",
            file_name=f"oa-filter-{seq}",
            file_size=1,
            path_origin=self.media_root,
        )

    def _create_learning_object_metadata(
        self,
        title,
        description,
        education_level,
        knowledge_area,
        license_obj,
        public,
        accesibility_features,
        accesibility_hazard,
        accesibility_control,
        annotation_modeaccess,
    ):
        """Crea un OA mínimo configurable para el buscador público.

        Cada prueba ajusta solo los campos que realmente intervienen en un
        filtro: titulo, descripción, catálogos y atributos de accesibilidad.
        """
        self._sequence += 1
        seq = self._sequence
        return LearningObjectMetadata.objects.create(
            learning_object_file=self._create_learning_object_file(seq),
            adaptation="none",
            avatar=self._build_avatar_png(),
            general_title=title,
            general_description=description,
            general_language="es",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
            user_created=self.teacher_user,
            public=public,
            accesibility_features=accesibility_features,
            accesibility_hazard=accesibility_hazard,
            accesibility_control=accesibility_control,
            annotation_modeaccess=annotation_modeaccess,
            annotation_modeaccesssufficient="",
            classification_purpose="",
        )

    def _result_ids(self, response):
        """Valida la respuesta paginada y extrae los IDs devueltos."""
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("results", response.data)
        return [item["id"] for item in response.data["results"]]

    def test_public_search_without_filters_returns_only_public_oas(self):
        """Sin filtros debe listar todos los OAs públicos y excluir el privado."""
        response = self.client.get("/api/v1/learning-objects/search/")
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 4)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_robotica.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertIn(self.oa_color_dependent.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_public_search_returns_avatar_with_domain(self):
        """El avatar debe salir con URL absoluta usando DOMAIN."""
        response = self.client.get("/api/v1/learning-objects/search/")
        self.assertEqual(response.status_code, 200, response.data)
        result = next(
            item for item in response.data["results"] if item["id"] == self.oa_python.id
        )
        self.oa_python.refresh_from_db()
        self.assertEqual(result["avatar"], DOMAIN + self.oa_python.avatar.url)

    def test_public_search_with_page_param_returns_only_public_oas(self):
        """page=1 no debe cambiar la regla base de excluir OAs privados."""
        response = self.client.get("/api/v1/learning-objects/search/?page=1")
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 4)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_robotica.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertIn(self.oa_color_dependent.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_annotation_modeaccess_accepts_color_depend_alias_from_front(self):
        """Acepta el alias legacy colorDepend usado por el frontend histórico."""
        response = self.client.get(
            "/api/v1/learning-objects/search/",
            {"annotation_modeaccess": "colorDepend"},
        )

        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(ids, [self.oa_color_dependent.id])

    def test_filter_combination_by_ids_and_license_value(self):
        """Permite combinar filtros por nivel, área y licencia al mismo tiempo."""
        response = self.client.get(
            "/api/v1/learning-objects/search/",
            {
                "education_levels__id": str(self.level_1.id),
                "knowledge_area__id": str(self.area_1.id),
                "license__value": self.license_1.value,
            },
        )
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 2)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertNotIn(self.oa_robotica.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_filter_general_title_keyword_matches_title_and_description(self):
        """general_title debe buscar por título y también por descripción."""
        response = self.client.get(
            "/api/v1/learning-objects/search/",
            {"general_title": "Python"},
        )
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 2)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertNotIn(self.oa_robotica.id, ids)

    def test_filter_accessibility_features_with_multiple_values_uses_or(self):
        """Valores repetidos de `accesibility_features` deben actuar como OR."""
        response = self.client.get(
            "/api/v1/learning-objects/search/?accesibility_features=captions&accesibility_features=audioDescription"
        )
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 2)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_robotica.id, ids)
        self.assertNotIn(self.oa_python_avanzado.id, ids)

    def test_recent_filter_returns_only_public_oas(self):
        """`recent=True` ordena por fecha, pero nunca debe devolver privados."""
        LearningObjectMetadata.objects.filter(pk=self.oa_python.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 10, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_robotica.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 11, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_python_avanzado.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 12, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_color_dependent.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 9, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_privado.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 13, 10, 0, 0))
        )

        response = self.client.get("/api/v1/learning-objects/search/?recent=True")
        ids = self._result_ids(response)

        self.assertEqual(response.data["count"], 4)
        self.assertEqual(ids[0], self.oa_python_avanzado.id)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_liked_filter_returns_only_public_oas(self):
        """liked=True solo debe listar OAs públicos aunque haya likes en privados."""
        Interaction.objects.create(
            liked=True,
            learning_object=self.oa_python,
            user=self.teacher_user,
        )
        Interaction.objects.create(
            liked=True,
            learning_object=self.oa_privado,
            user=self.teacher_user,
        )

        response = self.client.get("/api/v1/learning-objects/search/?liked=True")
        ids = self._result_ids(response)

        self.assertEqual(response.data["count"], 1)
        self.assertIn(self.oa_python.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_populars_endpoint_returns_only_public_oas(self):
        """populars/ no debe incluir OAs privados aunque tengan mejor rating."""
        EvaluationCollaboratingExpert.objects.create(
            learning_object=self.oa_python,
            rating=3.5,
            observation="Publico",
            collaborating_expert=self.teacher_user,
        )
        EvaluationCollaboratingExpert.objects.create(
            learning_object=self.oa_privado,
            rating=5.0,
            observation="Privado con rating alto",
            collaborating_expert=self.teacher_user,
        )

        response = self.client.get("/api/v1/learning-objects/populars/")

        self.assertEqual(response.status_code, 200, response.data)
        ids = [item["learning_object"]["id"] for item in response.data]
        self.assertIn(self.oa_python.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_learning_objects_most_recent_endpoint_returns_only_public_oas(self):
        """learning-objects-most-recent/ no debe incluir privados aunque sean más nuevos."""
        LearningObjectMetadata.objects.filter(pk=self.oa_python.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 10, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_robotica.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 11, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_python_avanzado.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 12, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_color_dependent.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 9, 10, 0, 0))
        )
        LearningObjectMetadata.objects.filter(pk=self.oa_privado.pk).update(
            created=timezone.make_aware(datetime(2026, 3, 13, 10, 0, 0))
        )

        response = self.client.get("/api/v1/learning-objects-most-recent/")

        self.assertEqual(response.status_code, 200, response.data)
        ids = [item["id"] for item in response.data]
        self.assertEqual(len(ids), 4)
        self.assertEqual(ids[0], self.oa_python_avanzado.id)
        self.assertNotIn(self.oa_privado.id, ids)

    def test_is_evaluated_false_keeps_public_filter_in_search(self):
        """is_evaluated=False mantiene la exclusión de privados en el buscador."""
        EvaluationCollaboratingExpert.objects.create(
            learning_object=self.oa_python,
            rating=3.0,
            observation="Evaluado por experto",
            collaborating_expert=self.expert_user,
        )
        EvaluationCollaboratingExpert.objects.create(
            learning_object=self.oa_privado,
            rating=4.0,
            observation="Privado evaluado por experto",
            collaborating_expert=self.expert_user,
        )
        api_client = APIClient()
        api_client.force_authenticate(user=self.expert_user)

        response = api_client.get("/api/v1/learning-objects/search/?is_evaluated=False")
        ids = self._result_ids(response)

        self.assertNotIn(self.oa_privado.id, ids)
        self.assertNotIn(self.oa_python.id, ids)
        self.assertIn(self.oa_robotica.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertIn(self.oa_color_dependent.id, ids)

    def test_filter_combination_title_year_and_access_control(self):
        """Permite combinar palabra clave, año de creación y control de acceso."""
        current_year = str(datetime.now().year)
        response = self.client.get(
            "/api/v1/learning-objects/search/",
            {
                "general_title": "Python",
                "created__year": current_year,
                "accesibility_control": "fullkeyboardcontrol",
            },
        )
        ids = self._result_ids(response)
        self.assertEqual(response.data["count"], 2)
        self.assertIn(self.oa_python.id, ids)
        self.assertIn(self.oa_python_avanzado.id, ids)
        self.assertNotIn(self.oa_privado.id, ids)
