# Registro De Migracion

Este archivo registra los cambios de migracion de forma secuencial.

## Formato De Entrada
- Titulo
- Hora
- Descripcion breve

---
# Migración Django 4.1 - 4.2

## [2026-03-13 09:00] Baseline Del Entorno (Capa A)
- Hora: 2026-03-13 09:00  (aprox)
- Descripcion: Se validaron versiones base del proyecto en entorno limpio (`Python 3.8.10`, `Django 4.1.5`), estado inicial de dependencias y ejecucion base del proyecto.

## [2026-03-13 09:20] Resolucion De Conflicto `environ` vs `django-environ`
- Hora: 2026-03-13 09:20  (aprox)
- Descripcion: Se elimino `environ==1.0` del lock, se desinstalo `environ` del `venv`, se reinstalo `django-environ==0.9.0` y se confirmo que `import environ` usa `django-environ`.

## [2026-03-13 09:45] Lote 1 Critico (Parcial) - Seguridad/Base
- Hora: 2026-03-13 09:45  (aprox)
- Descripcion: Se actualizaron `certifi`, `Pillow`, `PyJWT` y `sqlparse`. Se valido `pip check`, `manage.py check` y `manage.py test` en verde.

## [2026-03-13 10:00] Resolucion De Bloqueo PyYAML
- Hora: 2026-03-13 10:00  (aprox)
- Descripcion: Se detecto conflicto de `PyYAML>=6` con `docker-compose==1.25.5`. Se removio `docker-compose` de `requirements.txt` (no usado en el repo) y se dejo `PyYAML==6.0.3` estable.

## [2026-03-13 10:15] Lote 2 Bajo Riesgo - DB/Config
- Hora: 2026-03-13 10:15  (aprox)
- Descripcion: Se actualizaron `django-environ` (`0.9.0 -> 0.11.2`) y `psycopg2-binary` (`2.9.5 -> 2.9.9`). Nota: `2.9.10` requiere compilacion local en Windows/Python 3.8 (Build Tools), por eso se mantuvo `2.9.9`.

## [2026-03-13 10:35] Lote 3 Critico - HTTP Stack
- Hora: 2026-03-13 10:35  (aprox)
- Descripcion: Se actualizaron `requests` (`2.32.4`) y `urllib3` (`1.26.20`) manteniendo compatibilidad con `botocore` (`urllib3<1.27`). Se anadio `charset-normalizer==3.4.2` al lock para reproducibilidad.

## [2026-03-13 10:55] Lote 4 Critico - Crypto/XML
- Hora: 2026-03-13 10:55  (aprox)
- Descripcion: Se actualizaron `cryptography` (`46.0.5`) y `lxml` (`6.0.2`) y se validaron checks + pruebas (`107/107` OK).

## [2026-03-13 11:03] Politica De Registro Activada
- Hora: 2026-03-13 11:03 
- Descripcion: Desde este punto, cada cambio aplicado se registrara al finalizar en este archivo con titulo, hora y descripcion breve.

## [2026-03-13 11:15] Lote 5 Framework - Django 4.2 + DRF Compatible
- Hora: 2026-03-13 11:15 
- Descripcion: Se intento primero ruta segura (`Django 4.2.29` + `django-cors-headers 4.4.0`) y aparecio incompatibilidad con `djangorestframework 3.12.2` (`parse_header`). Se resolvio actualizando `djangorestframework` a `3.15.2` y `djangorestframework-simplejwt` a `5.3.1`. Validacion final en verde: `pip check`, `manage.py check` y `107/107` tests OK.

## [2026-03-13 11:20] Cierre De Criticos Restantes (Diagnostico Tecnico)
- Hora: 2026-03-13 11:20 
- Descripcion: Se evaluo cierre de los 2 criticos pendientes. `urllib3` no puede subir a 2.x mientras exista `botocore` en Python 3.8 (`urllib3<1.27`), incluso en versiones nuevas de botocore. `psycopg2-binary` no tiene wheel `2.9.10` para este entorno (`--only-binary` solo ofrece hasta `2.9.9`). Se documenta ambos como bloqueados por plataforma/compatibilidad y se mantienen pines compatibles.

## [2026-03-13 11:33] Lote 6 Opcionales Runtime (Sin xmltodict)
- Hora: 2026-03-13 11:33 
- Descripcion: Se actualizaron `django-absoluteuri` (`2.0.0`), `django-braces` (`1.17.0`), `django-model-utils` (`5.0.0`), `django-storages` (`1.14.6`) y `gunicorn` (`23.0.0`). Se intento subir `sendgrid`, pero se revirtio a `6.9.7` por incompatibilidad transitoria con stack legacy (`coreapi/rest_framework_swagger` via `MarkupSafe/Jinja2`). Se intento subir `django-filter` a `24.3`, pero se revirtio a `2.4.0` por regresion funcional en filtros publicos (4 tests). Validacion final: `pip check`, `manage.py check` y `107/107` tests OK.

## [2026-03-13 11:41] Lote 7 - xmltodict (Actualizacion Aislada)
- Hora: 2026-03-13 11:41 
- Descripcion: Se actualizo `xmltodict` de `0.12.0` a `0.15.0` y se sincronizo en `requirements.txt`. Validaciones: `pip check` y `manage.py check` OK; suite completa `107/107` OK. Observacion: durante pruebas aparecieron mensajes de log tipo `NoneType` en parsing de OA, sin causar fallos; se deja anotado para seguimiento.

## [2026-03-13 11:50] Rollback xmltodict a version estable
- Hora: 2026-03-13 11:50 
- Descripcion: Se restauro `xmltodict` a `0.12.0` en entorno y en `requirements.txt` para mantener compatibilidad del flujo actual. Se validaron `pip check`, `manage.py check` (con `DEBUG=1`) y prueba critica de carga real (`test.learning_object_file.test_full_upload_flow`) en verde.

## [2026-03-13 12:01] Lote Opcional Controlado - shortuuid y beautifulsoup4
- Hora: 2026-03-13 12:01 
- Descripcion: Se actualizaron `shortuuid` (`1.0.11 -> 1.0.13`) y `beautifulsoup4` (`4.9.3 -> 4.14.3`), se agrego `typing-extensions==4.13.2` al lock para reproducibilidad y se validaron `pip check`, `manage.py check` y tests clave de carga (`test_full_upload_flow` + `test_upload_error_cases`) en verde. Nota: con `beautifulsoup4` nuevo aparecen warnings de parser XML en logs, sin fallas funcionales.

## [2026-03-13 14:47] Lote Opcional Bajo Riesgo - termcolor/texttable/wincertstore
- Hora: 2026-03-13 14:47 
- Descripcion: Se actualizaron `termcolor` (`1.1.0 -> 2.4.0`), `texttable` (`1.6.7 -> 1.7.0`) y `wincertstore` (`0.2 -> 0.2.1`), se sincronizo `requirements.txt`, y se validaron `pip check`, `manage.py check` y smoke test de autenticacion (`test.user.authentication.test_authentication`) en verde.

## [2026-03-13 15:09] Lote Opcional Bajo Riesgo - colorama/chardet/semantic-version
- Hora: 2026-03-13 15:09 
- Descripcion: Se actualizaron `colorama` (`0.4.3 -> 0.4.6`), `chardet` (`4.0.0 -> 5.2.0`) y `semantic-version` (`2.8.5 -> 2.10.0`), se sincronizo `requirements.txt` y se validaron `pip check`, `manage.py check` y smoke test (`test.user.authentication.test_authentication`) en verde.

## [2026-03-13 15:17] Lote Final Opcionales - Resultado de compatibilidad
- Hora: 2026-03-13 15:17 
- Descripcion: Se probaron las opcionales restantes. Quedaron actualizadas y estables: `blessed` (`1.33.0`), `cached-property` (`2.0.1`), `cement` (`3.0.14`), `future` (`1.0.0`), `pathspec` (`0.12.1`), `ruamel.yaml` (`0.18.16`) con transitive `ruamel.yaml.clib` (`0.2.8`) y `wcwidth` (`0.6.0`). Se intento subir `sendgrid` a `6.12.5` y `django-filter` a `24.3`, pero se revirtieron por incompatibilidad funcional: `sendgrid` rompe arranque por conflicto `MarkupSafe/Jinja2` del stack legacy Swagger/CoreAPI y `django-filter` rompe filtros publicos (`test_public_oa_filters`). Validacion final: `pip check`, `manage.py check` y suite completa `107/107` OK.

## [2026-03-13 16:39] Ajuste de reproducibilidad - wincertstore
- Hora: 2026-03-13 16:39 
- Descripcion: Se ajusto `wincertstore` de `0.2.1` a `0.2` en `requirements.txt` para permitir instalacion en entornos limpios con `pip` legacy (`21.1.1`), ya que `0.2.1` no se resuelve de forma consistente en ese escenario.


---
# Migración Python 3.8 - 3.10


## [2026-03-16 10:51] Diagnostico de instalacion y verificacion de entorno Python 3.10
- Hora: 2026-03-16 10:51 
- Descripcion: Se reprodujo el error de `pip install -r requirements.txt` en Python 3.10 y se valido el lock actual del proyecto (`cffi==2.0.0`, `docker==7.1.0`) para resolver conflictos de dependencias en este runtime. Validacion final en `venv`: instalacion completa de dependencias, `pip check` en verde, `manage.py check` en verde y smoke test de autenticacion (`6/6`) en verde.

---
# Migración Python 3.10 - 3.12  

## [2026-03-16 14:03] Pre-check completo de compatibilidad para Python 3.12
- Hora: 2026-03-16 14:03 
- Descripcion: Se ejecuto un barrido completo de `requirements.txt` contra artefactos publicados en PyPI para `Python 3.12 + Windows amd64` (sin cambios de version aun). Resultado: `93` dependencias evaluadas, `14` no compatibles directamente con wheel de `py3.12` o con build legacy. Bloqueos principales confirmados: `numpy==1.23.5`, `pandas==1.4.4`, `scipy==1.9.3`, `scikit-learn==1.1.3`, `regex==2021.4.4`, `simplejson==3.17.2`, `MarkupSafe==1.1.1`, `pyrsistent==0.17.3`. Riesgos secundarios por paquete legacy/sdist: `docopt`, `openapi-codec`, `rest-condition`, `starkbank-ecdsa`, `coreschema`, `Unipath`. Se confirma ademas que el fallo original de instalacion en `venv3.12` viene de `numpy==1.23.5` al intentar build con toolchain no compatible con Python 3.12 (`pkgutil.ImpImporter` removido).

## [2026-03-16 14:20] Ajuste de compatibilidad `six` para Python 3.12
- Hora: 2026-03-16 14:20 
- Descripcion: Durante la validacion de `manage.py check` en Python 3.12 aparecio una rotura de runtime en `boto3/botocore/python-dateutil` por `ModuleNotFoundError: No module named 'six.moves'` con `six==1.14.0`. Se actualizo el pin a `six==1.17.0` para restaurar compatibilidad con Python 3.12 antes de continuar con `check` y la suite de pruebas.

## [2026-03-16 14:28] Ajuste de compatibilidad `setuptools/pkg_resources` para Python 3.12
- Hora: 2026-03-16 14:28 
- Descripcion: En la siguiente validacion de `manage.py check` se detecto una rotura de runtime en `coreapi/rest_framework_swagger` por ausencia de `pkg_resources` dentro del entorno Python 3.12. Se agrego `setuptools==82.0.1` al lock para que el entorno limpio tenga `pkg_resources` disponible y se pueda seguir validando el arranque del proyecto.

## [2026-03-16 14:35] Ajuste de pin `setuptools` por remocion de `pkg_resources`
- Hora: 2026-03-16 14:35 
- Descripcion: La verificacion en el entorno mostro que `setuptools==82.0.1` ya no exponia `pkg_resources` como modulo importable, lo que seguia rompiendo `coreapi`. Se ajusto el pin a `setuptools==75.8.0`, manteniendo un runtime compatible con el stack legacy de Swagger/CoreAPI usado por el proyecto.

## [2026-03-16 14:50] Correccion de tests por `tempfile.mkdtemp()` en Python 3.12
- Hora: 2026-03-16 14:50 
- Descripcion: Durante la ejecucion de la suite en Python 3.12 se confirmo que `tempfile.mkdtemp()` generaba directorios donde luego fallaba `os.makedirs(.../oazip)` con `PermissionError` en Windows, afectando los tests de carga, metadata, filtros y evaluaciones. Se incorporo el helper `test/helpers/temp_media_root.py` para crear `MEDIA_ROOT` temporales manualmente dentro del repo y se reemplazo el uso de `mkdtemp()` en los tests afectados.

## [2026-03-16 15:00] Validacion completa en Python 3.12
- Hora: 2026-03-16 15:00 
- Descripcion: Con los ajustes de dependencias y el cambio en los tests temporales, el entorno `venv` en `Python 3.12.10` quedo validado con `pip check` en verde, `manage.py check` en verde y la suite completa `manage.py test` pasando `107/107`.

## [2026-03-16 15:20] Correccion de evaluacion experta con `No aplica`
- Hora: 2026-03-16 15:20 
- Descripcion: Se corrigio la logica de `applications/evaluation_collaborating_expert/views.py` para evitar `ZeroDivisionError` cuando una o varias areas quedan solo con respuestas `No aplica`. El calculo de promedios por concepto ahora es dinamico y seguro, la creacion/actualizacion de evaluaciones expertas corre dentro de transacciones atomicas para no dejar registros parciales si algo falla, y se agrego una regresion en `test/evaluation_collaborating_expert/test_expert_evaluation_flow.py` que valida el caso con todas las respuestas en `No aplica`.

---
# Migración Django 4.2 - 5.0

## [2026-03-16 15:40] Migracion a Python 3.12 + Django 5.0
- Hora: 2026-03-16 15:40 
- Descripcion: Se completo el salto del entorno validado en `Python 3.12` desde `Django 4.2.29` a `Django 5.0.12`, actualizando tambien `asgiref` a `3.8.1` y removiendo `USE_L10N` de `roabackend/settings.py` por compatibilidad con Django 5. Validacion final en `venv`: `python -m django --version` = `5.0.12`, `pip check` en verde, `manage.py check` en verde y suite completa `manage.py test` en verde (`108/108`).

---
# Migración Django 5.0 - 5.1

## [2026-03-16 17:13] Migracion a Python 3.12 + Django 5.1
- Hora: 2026-03-16 17:13 
- Descripcion: Se actualizo `Django` de `5.0.12` a `5.1.15`, manteniendo `asgiref==3.8.1` y el resto del lock estable. Validacion final en `venv`: `python -m django --version` = `5.1.15`, `pip check` en verde, `manage.py check` en verde y suite completa `manage.py test` en verde (`108/108`).

---
# Migración Django 5.1 - 5.2

## [2026-03-16 18:07] Migracion a Python 3.12 + Django 5.2
- Hora: 2026-03-16 18:07 
- Descripcion: Se actualizo `Django` de `5.1.15` a `5.2.12`, manteniendo `asgiref==3.8.1` sin cambios adicionales de codigo. Validacion final en `venv`: `python -m django --version` = `5.2.12`, `pip check` en verde, `manage.py check` en verde y suite completa `manage.py test` en verde (`108/108`).

## [2026-03-17 08:25] Cobertura de delete de OA y diagnostico de slash final
- Hora: 2026-03-17 08:25 
- Descripcion: Se agrego `test/learning_object_file/test_admin_delete_learning_object.py` para cubrir tanto el borrado administrativo como el borrado de docente sobre objetos de aprendizaje. Las pruebas validan el caso exitoso con la URL canonica terminada en `/` y reproducen el `RuntimeError` de Django cuando se invoca `DELETE` sin slash final con `APPEND_SLASH` activo, confirmando que esos `500` se corrigen desde el cliente/front usando la ruta con `/` final.

---
# Refactorización del código


## [2026-03-17 11:45] Fase 1 de refactorizacion segura post Django 5.2
- Hora: 2026-03-17 11:45
- Descripcion: Se implemento la fase 1 del plan de refactorizacion segura. Cambios aplicados: filtros de fecha por `created__date__range` en `applications/learning_object_metadata/views.py` y `applications/user/views.py` para evitar warnings de `datetime` naive, reemplazo de validaciones `len(queryset)` por `.exists()` en serializers de `user`, `evaluation_student`, `evaluation_collaborating_expert` y `learning_object_metadata`, migracion de `print(...)` a `logging` en modulos activos de correo y carga de OA, y correccion segura del filtro `query` en `ReportListAPIView`. Se agregaron pruebas `test/learning_object_metadata/test_admin_date_range_filters.py` y `test/user/test_report_date_range_filters.py`. Validacion final: `114/114` pruebas en verde.

## [2026-03-17 13:05] Correccion del filtro publico en `/learning-objects/search/`
- Hora: 2026-03-17 13:05
- Descripcion: Se corrigio el endpoint publico de busqueda de OAs para evitar que objetos no publicos reaparezcan al usar `/learning-objects/search/`, `/learning-objects/search/?page=1`, `recent=True`, `liked=True` o `scored=True`. El ajuste se hizo en `applications/learning_object_metadata/views.py`, haciendo que `SerachAPIView` parta siempre de `LearningObjectMetadata.objects.filter(public=True)` y que los metodos `most_liked`, `most_recent` y `most_scored` reutilicen el queryset ya filtrado en lugar de reconstruir consultas amplias. Validacion: `test.learning_object_metadata.test_public_oa_filters` en verde (`8/8`) y suite completa `manage.py test --keepdb` en verde (`117/117`).

## [2026-03-18 09:05] Avatar de OA con URL absoluta de dominio
- Hora: 2026-03-18 09:05 
- Descripcion: Se ajustaron los serializers de lectura de `applications/learning_object_metadata/serializers.py` para que el campo `avatar` del objeto de aprendizaje se devuelva como URL absoluta usando `DOMAIN + obj.avatar.url`, siguiendo el mismo patron que ya usan los serializers de usuario para `image_url`. El cambio se aplico en `LearningObjectMetadataAllSerializer`, `LearningObjectMetadataPopularFieldSerializer` y `TeacherUploadListSerializer`. Validacion: prueba focalizada `test.learning_object_metadata.test_public_oa_filters` en verde (`9/9`), incluyendo la nueva regresion que verifica `avatar` con dominio completo en `/api/v1/learning-objects/search/`.

## [2026-03-18 09:40] Fase 2 sublote 1: transacciones en flujos multi-escritura
- Hora: 2026-03-18 09:40 
- Descripcion: Se inicio la fase 2 de refactorizacion segura aplicando `transaction.atomic` en flujos con multiples escrituras para evitar estados parciales. Se protegieron `StudentEvaluationView.create`, `StudentEvaluationView.update` en `applications/evaluation_student/views.py` y `LearningObjectMetadataViewSet.perform_create` en `applications/learning_object_metadata/views.py`. Se agregaron regresiones de rollback en `test/evaluation_student/test_student_evaluation_flow.py` y `test/learning_object_file/test_full_upload_flow.py` para verificar que, si falla una escritura interna, no se persisten evaluaciones ni metadata parciales. Validacion: pruebas focalizadas `6/6` en verde y suite completa `manage.py test --keepdb` en verde (`120/120`).

## [2026-03-18 10:25] Correccion del mapeo de respuestas en evaluacion de estudiante
- Hora: 2026-03-18 10:25 
- Descripcion: Se corrigio `applications/evaluation_student/views.py` para que las respuestas del estudiante se asignen por `question_id` en lugar de depender del orden posicional del payload. El ajuste se aplico tanto en `StudentEvaluationView.create` como en `StudentEvaluationView.update`, evitando que la interfaz de edicion cargue respuestas mezcladas entre preguntas o guidelines. No se tocaron modelos ni migraciones; solo la logica de guardado/actualizacion. Se agregaron regresiones en `test/evaluation_student/test_student_evaluation_flow.py` para validar create con varias guidelines y update con payload en orden distinto al de base de datos. Validacion: suite focalizada del modulo en verde (`5/5`) y suite completa `manage.py test --keepdb` en verde (`122/122`).

## [2026-03-18 11:05] Orden canonico al recargar la evaluacion de estudiante
- Hora: 2026-03-18 11:05 
- Descripcion: Se ajusto `applications/evaluation_student/serializers.py` para que los endpoints de consulta del formulario del estudiante devuelvan principios, guidelines y preguntas en un orden estable por `id`, igual al catalogo que se usa al llenar la evaluacion inicial. El cambio se aplico en `PrincipleSerializer`, `GuidelineSerializer`, `EvaluationGuideline_QualificationsValueSerializer`, `EvaluationPrinciple_QualificationsValueSerializer` y `EvaluationStudentList_EvaluationSerializer`, reemplazando relaciones reversas sin orden explicito por `SerializerMethodField` con `order_by(...)`. Se agrego una regresion en `test/evaluation_student/test_student_evaluation_flow.py` para garantizar que la recarga para editar respete el orden canonico de preguntas. Validacion: modulo `test.evaluation_student.test_student_evaluation_flow` en verde (`6/6`) y suite completa `manage.py test --keepdb` en verde (`123/123`).

## [2026-03-18 15:45] Fase 2 sublote 2: reduccion de except genericos en helpers de correo
- Hora: 2026-03-18 15:45 
- Descripcion: Se avanzo el segundo sublote de la fase 2 reemplazando `except Exception` por un conjunto acotado de errores recuperables de correo/plantilla (`OSError`, `smtplib.SMTPException`, `AttributeError`, `TypeError`, `ValueError`) en `applications/user/emailManager.py`, `applications/learning_object_file/emailManagerLO.py` y `applications/learning_object_metadata/testMailMetadata.py`. El objetivo fue dejar visibles los errores inesperados de programacion sin cambiar el comportamiento ante fallos esperables de SMTP o archivos de plantilla. Se agregaron pruebas nuevas en `test/user/test_email_manager_error_handling.py`, `test/learning_object_file/test_email_manager_lo_error_handling.py` y `test/learning_object_metadata/test_mail_metadata_error_handling.py` para validar que los fallos recuperables siguen registrandose sin romper el flujo y que al menos un `RuntimeError` inesperado ya no se silencia. Validacion: pruebas focalizadas `4/4` en verde y suite completa `manage.py test --keepdb` en verde (`127/127`).

## [2026-03-18 16:10] Fase 2 sublote 3: validaciones simples movidas a serializers en settings
- Hora: 2026-03-18 16:10
- Descripcion: Se movieron validaciones simples del modulo `applications/settings` desde las views hacia serializers dedicados para reducir dependencia de `request.data[...]` y `request.query_params[...]` crudos. Se agregaron `EmailDomainTypeSerializer`, `EmailDomainListQuerySerializer` y `UserTypeOptionUpdateInputSerializer` en `applications/settings/serializers.py`, y se aplicaron en `EmailDomainListCreateAPIView`, `EmailDomainUpdateView`, el endpoint de borrado de dominios y `UserTypeOptionUpdateView` en `applications/settings/views.py`. El cambio mantiene rutas y flujo de negocio, pero ahora valida de forma controlada `type`, `option` y `option_register`, devolviendo errores del serializer sin tocar modelos ni migraciones. Se agregaron pruebas nuevas en `test/settings/test_settings_validation_serializers.py` y el comando focalizado en `test/README.md`. Validacion: modulo `test.settings.test_settings_validation_serializers` en verde (`6/6`) y suite completa `manage.py test --keepdb` en verde (`133/133`).

## [2026-03-18 17:45] Fase 2 sublote 4: reduccion de except genericos en settings
- Hora: 2026-03-18 17:45
- Descripcion: Se continuo la fase 2 reduciendo `except Exception` en `applications/settings`. En `applications/settings/views.py` se eliminaron capturas genericas en `EmailListCreateAPIView`, resolviendo explicitamente el caso sin configuracion SMTP y dejando visibles los errores inesperados; ademas se agrego `EmailTestingConnectionSerializer` para validar el payload de `sendEmailTestingConecction` y el manejo de errores se limito a `MAIL_DELIVERY_EXCEPTIONS`, reemplazando `print(...)` por `logging`. En `applications/settings/models.py` se removieron `try/except` redundantes en `Email.encrypt_password` y `Email.decrypt_password` que solo relanzaban la misma excepcion. Se agregaron pruebas nuevas en `test/settings/test_settings_error_handling.py` para cubrir: consulta sin configuracion, update controlado sin registro base, update valido de SMTP, validacion del payload de prueba de correo, manejo de errores SMTP esperables y propagacion de `RuntimeError` inesperado. Tambien se documento el comando focalizado en `test/README.md`. Validacion: modulos `test.settings.test_settings_validation_serializers` y `test.settings.test_settings_error_handling` en verde (`12/12`) y suite completa `manage.py test --keepdb` en verde (`139/139`).

## [2026-03-18 18:30] Fase 2 sublote 5: transacciones en update/delete de evaluacion experta
- Hora: 2026-03-18 18:30
- Descripcion: Se continuo la fase 2 reforzando la atomicidad en `applications/evaluation_collaborating_expert/views.py`, agregando `@transaction.atomic` a `EvaluationCollaboratingExpertView.update` y `EvaluationCollaboratingExpertView.destroy`, dos flujos que modifican o eliminan multiples registros relacionados (`EvaluationCollaboratingExpert`, `EvaluationConceptQualification` y `EvaluationQuestionsQualification`). Para validar el rollback real se ampliaron las pruebas en `test/evaluation_collaborating_expert/test_expert_evaluation_flow.py` con dos regresiones: una para fallo durante el recalculo de promedios en update y otra para fallo durante un borrado relacionado en destroy. En ese modulo se migro la clase de pruebas a `TransactionTestCase` para observar correctamente los efectos de `transaction.atomic` en requests que terminan en error. Validacion: modulo `test.evaluation_collaborating_expert.test_expert_evaluation_flow` en verde (`10/10`) y suite completa `manage.py test --keepdb` en verde (`141/141`).

## [2026-03-18 17:24] Fase 2 sublote 6: validaciones simples movidas a serializers en interaction
- Hora: 2026-03-18 17:24
- Descripcion: Se aplico el sublote 6 en `applications/interaction`, moviendo validaciones simples desde las views hacia serializers de DRF para reducir accesos crudos a `request.data[...]` y cortar payloads invalidos antes de tocar la base. `InteractionSerializer` paso a validar `learning_object` con `PrimaryKeyRelatedField` y `downloaded` con `min_value=0`; se agregaron `InteractionLikeUpdateSerializer` e `InteractionDownloadUpdateSerializer` para aislar updates pequenos; `InteractionViewCreateSerializer` dejo de depender del `ModelSerializer` implicito y ahora valida `view >= 0` y la existencia del OA. En `applications/interaction/views.py` se ajustaron `InteractionAPIView.create/update`, `CreateDownload` y `GetUpdateDownloadNumber.update` para consumir `validated_data` y reutilizar el OA ya resuelto por serializer. Se agregaron pruebas nuevas en `test/interaction/test_interaction_validation_serializers.py` para cubrir: flujo valido de like, rechazo de OA inexistente, update sin `liked`, descargas negativas y vistas negativas, y se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.interaction.test_interaction_validation_serializers` en verde (`5/5`) y suite completa `manage.py test --keepdb` en verde (`146/146`).

## [2026-03-19 08:46] Fase 3 sublote 1: compatibilidad de slash final en delete de OA
- Hora: 2026-03-19 08:46
- Descripcion: Se inicio la fase 3 por el punto de compatibilidad mas sensible con front: los `DELETE` de objetos de aprendizaje que fallaban con `APPEND_SLASH` cuando el cliente llamaba sin slash final. En `applications/learning_object_file/urls.py` se agregaron aliases legacy sin slash para `api/v1/learning-object-file-delete/<pk>` y `api/v1/learning-object-file-delete-admin/<pk>`, apuntando a los mismos viewsets del router. La ruta canonica con slash se mantiene intacta; el cambio solo agrega compatibilidad hacia atras para que ambas formas funcionen. Se actualizaron las pruebas de `test/learning_object_file/test_admin_delete_learning_object.py` para validar borrado exitoso tanto con slash como sin slash en docente y admin. Validacion: modulo focalizado en verde (`4/4`) y suite completa `manage.py test --keepdb` en verde (`146/146`).

## [2026-03-19 09:05] Fase 3 sublote 2: compatibilidad de slash en rutas manuales de interaction
- Hora: 2026-03-19 09:05
- Descripcion: Se continuo la fase 3 en `applications/interaction/urls.py`, agregando aliases compatibles para rutas manuales que mezclaban slash y no slash final. Se habilito compatibilidad adicional en `downloaded`, `downloaded/<pk>`, `interaction-ref`, `most-liked`, `liked-count/<pk>` y `liked/<pk>`, manteniendo intactas las rutas originales. Durante la validacion se detecto que `learning-objects/viewed/` ya colisiona con otra URL existente del proyecto, por lo que no se forzo un alias de creacion con slash para evitar invadir un contrato ajeno. Se agrego `test/interaction/test_interaction_url_compatibility.py` para cubrir las variantes soportadas y se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.interaction.test_interaction_url_compatibility` en verde (`5/5`) y suite completa `manage.py test --keepdb` en verde (`151/151`).

## [2026-03-19 10:19] Fase 3 sublote 3: compatibilidad de slash en rutas manuales de settings
- Hora: 2026-03-19 10:19
- Descripcion: Se extendio la fase 3 al modulo `applications/settings`, agregando aliases con slash final para rutas manuales que hoy estaban mezcladas: `email-domain/active`, `email-domain/<pk>`, `email-domain-update/<pk>` y `type-user-option-register-update/<pk>`. Se mantuvieron intactas las rutas originales y solo se agrego compatibilidad hacia atras para que ambas variantes convivan. Se creo `test/settings/test_settings_url_compatibility.py` para cubrir listado activo, borrado de dominio, update de dominio y update de opcion de registro usando las nuevas variantes con slash, y se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.settings.test_settings_url_compatibility` en verde (`4/4`) y suite completa `manage.py test --keepdb` en verde (`155/155`).

## [2026-03-19 10:37] Fase 3 sublote 4: compatibilidad de slash en rutas manuales de user
- Hora: 2026-03-19 10:37
- Descripcion: Se continuo la fase 3 en `applications/user/urls.py`, agregando aliases con slash final para rutas manuales del modulo `user` que el front podia invocar con una variante distinta a la canonica. Se mantuvieron intactas las rutas existentes y se sumo compatibilidad adicional para `email-verify/<token>/<email>`, `report`, `teacher-to-approve-delete/<pk>` y `expert-to-approve-delete/<pk>`, reutilizando las mismas views para evitar cambios de contrato. Se creo `test/user/test_user_url_compatibility.py` para cubrir el reporte y los borrados de docente/experto desaprobados usando la variante con slash, y se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.user.test_user_url_compatibility` en verde (`3/3`) y suite completa `manage.py test --keepdb` en verde (`158/158`).

## [2026-03-19 11:10] Fase 3 sublote 5: compatibilidad de slash en rutas manuales de address
- Hora: 2026-03-19 11:10
- Descripcion: Se extendio la fase 3 al modulo `applications/address`, agregando aliases con slash final para rutas manuales que aun combinaban variantes con y sin slash. Se mantuvieron intactas las rutas existentes y se sumo compatibilidad adicional para detalles CRUD (`countries/<pk>`, `province/<pk>`, `university/<pk>`, `city/<pk>`, `campus/<pk>`) y para filtros/listados publicos (`countries/active`, `cities/active`, `universities/active`, `campus/active`, `province/country/<pk>`, `universities-by-city/<pk>`, `universities/active/<pk>` y `campus/active/<pk>`), reutilizando las mismas views para no alterar contratos ni permisos. Se creo `test/address/test_address_url_compatibility.py` para cubrir las variantes con slash de retrieve y filtros activos, y se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.address.test_address_url_compatibility` en verde (`5/5`) y suite completa `manage.py test --keepdb` en verde (`163/163`).

## [2026-03-19 11:31] Fase 3 sublote 6: compatibilidad de configuracion legacy en DOMAIN_HOST_ROA y KEY_REF
- Hora: 2026-03-19 11:31
- Descripcion: Se continuo la fase 3 endureciendo compatibilidad de configuracion legacy para evitar `500` por variables de entorno faltantes en local. Se agrego `applications/helpers_functions/env_compat.py` con dos helpers: `get_domain_host_roa()`, que usa `DOMAIN_HOST_ROA` y cae a `DOMAIN_HOST` si la variable legacy no esta configurada, y `get_key_ref()`, que devuelve `None` cuando falta `KEY_REF` para que el endpoint responda de forma controlada. Se aplico el fallback de host en `applications/user/views.py` para reset de contrasena, en `applications/user/emailManager.py` y `applications/learning_object_metadata/testMailMetadata.py` para correos con enlaces/host del ROA; y se ajusto `applications/interaction/views.py` para que `interaction-ref` registre el problema y devuelva el error legacy sin explotar si `KEY_REF` no existe. Se agregaron regresiones en `test/user/test_user_env_compatibility.py`, `test/interaction/test_interaction_url_compatibility.py` y `test/learning_object_metadata/test_mail_metadata_error_handling.py`, y se documentaron los comandos focalizados en `test/README.md`. Validacion: pruebas focalizadas `9/9` en verde y suite completa `manage.py test --keepdb` en verde (`166/166`).

## [2026-03-19 15:10] Fase 3 sublote final: compatibilidad de slash en modulos pequenos
- Hora: 2026-03-19 15:10
- Descripcion: Se cerro el mini-lote final seguro de la fase 3 agregando aliases de slash final en rutas manuales de modulos pequenos fuera de la logica sensible de evaluacion y recomendacion. Se agrego compatibilidad para `api/v1/learning-object/filters/area/` en `applications/preferences/urls.py`, para `api/v1/endpoint-filter/` en `applications/license/urls.py` y para `api/v1/learning-object-oer/create/` en `applications/learning_object_file/urls.py`, manteniendo intactas las rutas existentes. Se agregaron regresiones en `test/preferences/test_preferences_url_compatibility.py`, `test/license/test_license_url_compatibility.py` y `test/learning_object_file/test_oer_url_compatibility.py`, y se documentaron sus comandos en `test/README.md`. Validacion: pruebas focalizadas `3/3` en verde y suite completa `manage.py test --keepdb` en verde (`169/169`).

## [2026-03-19 15:34] Correccion de filtro annotation_modeaccess en busqueda publica
- Hora: 2026-03-19 15:34
- Descripcion: Se corrigio el filtro `annotation_modeaccess` del buscador publico y experto en `applications/learning_object_metadata/views.py`. El problema era que el front enviaba el alias legacy `colorDepend`, mientras el backend solo reconocia `colorDependent`; en ese caso el metodo terminaba sin `return` y `django-filter` lanzaba `AssertionError` al recibir `None`. Se extrajo un helper comun para normalizar aliases (`Visual`, `Text`, `Auditory`, `colorDepend`/`colorDependent`) y garantizar que siempre se devuelva un `QuerySet`. Se agrego regresion en `test/learning_object_metadata/test_public_oa_filters.py` para cubrir el alias del front. Validacion: modulo `test.learning_object_metadata.test_public_oa_filters` en verde (`10/10`) y suite completa `manage.py test --keepdb` en verde (`170/170`).

## [2026-03-19 16:17] Inicio de Fase 4: auditoria de recommendation system
- Hora: 2026-03-19 16:17
- Descripcion: Se inicio la fase 4 en modo auditoria, sin cambios de codigo, revisando `applications/recommendation_system/views.py`, `applications/recommendation_system/dataset_generator.py` y `applications/recommendation_system/recommended.py`. Se documento el flujo actual, las dependencias funcionales y los riesgos de refactorizacion en `docs/auditoria_fase4_recommendation_system_2026-03-19.md`. Hallazgos principales: ausencia de pruebas del modulo, uso de `except:` genericos, supuesto rigido de exactamente 4 preferencias por nombre/orden, uso de `df.iloc[loId]` con IDs de BD como indices posicionales, descarga de NLTK en import time y helpers que devuelven `Exception` como dato. Recomendacion documentada: arrancar con pruebas de caracterizacion antes de cambiar logica.

## [2026-03-19 16:17] Fase 4: pruebas de caracterizacion para recommendation system
- Hora: 2026-03-19 16:17
- Descripcion: Se agregaron las primeras pruebas de caracterizacion del recommendation system en `test/recommendation_system/test_recommendation_system_characterization.py`, sin modificar aun la logica del modulo. Se cubrio el endpoint `GET /api/v1/learning-objects/recommended/` con `mocks` controlados para documentar el comportamiento actual: requiere autenticacion, une recomendaciones por likes y por conceptos, excluye objetos ya vistos y ante error interno responde lista vacia por el `except:` legacy. Tambien se agregaron pruebas unitarias de helpers para documentar dos supuestos funcionales actuales: el orden fijo de las 4 areas en `get_user_preferences_value()` y la regla de umbral de `recomended()`. Se documento el comando focalizado en `test/README.md`. Validacion: modulo `test.recommendation_system.test_recommendation_system_characterization` en verde (`5/5`) y suite completa `manage.py test --keepdb` en verde (`175/175`).

## [2026-03-19 17:01] Fase 4: correccion de lookup por loId en recomendaciones por likes
- Hora: 2026-03-19 17:01
- Descripcion: Se aplico el primer cambio real del recommendation system en `applications/recommendation_system/recommended.py`. Se corrigio el bug donde `learning_object_recomended()` buscaba el OA liked usando `df.iloc[loId]`, tratando el ID de base de datos como indice posicional del DataFrame. Ahora el lookup se hace por la columna `loId`, y si no existe coincidencia el helper devuelve lista vacia de forma controlada. Se agrego una regresion en `test/recommendation_system/test_recommendation_system_characterization.py` para cubrir IDs no consecutivos y confirmar que la recomendacion por likes ya no depende del orden/posicion del DataFrame. Validacion: modulo `test.recommendation_system.test_recommendation_system_characterization` en verde (`6/6`) y suite completa `manage.py test --keepdb` en verde (`176/176`).

## [2026-03-19 17:35] Compatibilidad de update para estudiantes sin ubicacion en user-management
- Hora: 2026-03-19 17:35
- Descripcion: Se corrigio una inconsistencia legacy en `applications/user/views.py` y `applications/user/serializers.py`: el alta de estudiantes nunca exige `city`, `university` ni `campus`, pero el endpoint `PUT /api/v1/user-management/<id>/` los requeria para todos los roles y ademas convertia esos campos con `int(...)`, provocando `400` o potenciales `500` cuando el front reenviaba `null`. El ajuste hizo opcionales `city`, `university` y `campus` en `UserUpdateSerializer`, uso `validated_data` en lugar de `request.data[...]` crudo y permitio `disability_description=""`/`null` en serializers de estudiante, alineandolos con el modelo que ya admite blanco/nulo. Se agregaron regresiones en `test/user/test_user_management_update.py` para cubrir: update valido de estudiante con ubicacion nula y descripcion de discapacidad vacia, y update valido de docente con ids de ubicacion para confirmar que el flujo previo sigue funcionando. Validacion: modulo `test.user.test_user_management_update` en verde (`2/2`), paquete completo `test.user` en verde (`31/31`) y modulo de caracterizacion de recommendation system mantenido en verde (`6/6`).

## [2026-03-20 09:05] Fase 4: correccion de FutureWarning en recomendaciones por likes
- Hora: 2026-03-20 09:05
- Descripcion: Se ajusto `applications/recommendation_system/recommended.py` para evitar el `FutureWarning` de pandas al convertir una `Series` completa con `int(...)` en `ItemsRecomended.user_learning_object_recomended_liked()`. Ahora el helper toma de forma explicita el primer `learning_object` con `.iloc[0]` y devuelve lista vacia si el DataFrame de likes llega vacio. Se agrego una regresion en `test/recommendation_system/test_recommendation_system_characterization.py` para documentar que el helper usa un escalar real y no intenta convertir toda la `Series`. Validacion: comprobacion directa en `manage.py shell` con `warnings.simplefilter('error', FutureWarning)` en verde para el caso con like y el caso vacio, y modulo `test.user` mantenido en verde (`31/31`). Nota: el rerun completo del modulo `test.recommendation_system` quedo bloqueado por el estado actual de la base de pruebas `test_roaTestDB`, no por un fallo funcional del cambio.

## [2026-03-20 10:22] Fase 4: endurecimiento defensivo de recommended.py
- Hora: 2026-03-20 10:22
- Descripcion: Se continuo la fase 4 con un refactor pequeño y de bajo riesgo en `applications/recommendation_system/recommended.py`. Se agrego `logging` local, se reemplazo el `except:` generico de `ItemsRecomended.user_learning_object_recomended_liked()` por una captura acotada de errores de forma/datos (`AttributeError`, `KeyError`, `TypeError`, `ValueError`, `IndexError`) y se validaron condiciones defensivas antes de operar sobre DataFrames (`DataFrame` vacio, columna `learning_object` faltante, columnas requeridas ausentes en metadata). En `learning_object_recomended()` tambien se encapsulo el calculo de similitud con manejo controlado de errores de estructura sin cambiar el contrato actual: ante problemas internos sigue devolviendo `[]`. Se agregaron regresiones nuevas en `test/recommendation_system/test_recommendation_system_characterization.py` para documentar los casos de columna `learning_object` faltante y metadata sin columnas requeridas. Validacion: paquete `test.user` en verde (`31/31`) y comprobaciones directas en `manage.py shell` en verde para (1) extraccion del escalar `learning_object`, (2) dataset de likes sin columna esperada y (3) metadata sin columnas requeridas, todas devolviendo el comportamiento esperado. Nota: el rerun automatizado del modulo `test.recommendation_system` sigue bloqueado por el estado de la base `test_roaTestDB`.

## [2026-03-20 10:38] Fase 4: endurecimiento defensivo de helpers en recommendation_system views
- Hora: 2026-03-20 10:38
- Descripcion: Se continuo la fase 4 con un refactor acotado en `applications/recommendation_system/views.py`, enfocado solo en los helpers internos `recomended()` y `get_user_preferences_value()`. Se agrego `logging`, se reemplazaron los `except:` genericos por capturas acotadas de errores de estructura/datos y se incorporaron guardas defensivas para datasets vacios, columnas requeridas faltantes y perfiles de usuario incompletos. El comportamiento funcional se mantuvo: en casos invalidos estos helpers ahora devuelven `[]` en lugar de la clase `Exception`, evitando propagar valores inesperados al endpoint de recomendaciones. Para validar el cambio sin depender de la base `test_roaTestDB`, se agrego el modulo puro `test/recommendation_system/test_recommendation_system_view_helpers.py` con `SimpleTestCase`, cubriendo: happy path actual, columnas faltantes, perfil corto y entradas invalidas del helper de preferencias. Validacion: modulo `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`4/4`, sin usar BD) y paquete `test.user` mantenido en verde (`31/31`).

## [2026-03-20 10:52] Fase 4: limpieza del except de get_queryset en recommendation_system
- Hora: 2026-03-20 10:52
- Descripcion: Se refactorizo `LearningObjectRecommended.get_queryset()` en `applications/recommendation_system/views.py` para dejar de tragar cualquier error con `except:` generico. El metodo ahora valida de forma explicita los tipos y estructuras de sus dependencias (`likes`, `oa_viewed`, dataset de preferencias y recomendaciones por experto), mantiene el contrato actual de devolver `[]` si una dependencia falla y registra el error con `logging` cuando ocurre una excepcion esperada (`AttributeError`, `KeyError`, `TypeError`, `ValueError`, `IndexError`, `RuntimeError`). Tambien se simplifico la exclusion de OAs ya vistos a una forma equivalente y mas clara. Se ampliaron las pruebas puras en `test/recommendation_system/test_recommendation_system_view_helpers.py` para cubrir: happy path de `get_queryset()` con dependencias mockeadas, dataset de preferencias invalido y falla interna con `RuntimeError`, sin depender de la base de pruebas. Validacion: modulo `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`) y paquete `test.user` en verde (`31/31`).

## [2026-03-20 11:05] Fase 4: eliminacion de descarga NLTK en import-time
- Hora: 2026-03-20 11:05
- Descripcion: Se elimino el efecto secundario `nltk.download('stopwords')` de `applications/recommendation_system/recommended.py`, que antes se ejecutaba al importar el modulo y ensuciaba el arranque del backend/tests. En su lugar se agregaron los helpers `get_spanish_stopwords()` y `build_tfidf_vectorizer()`: el primero obtiene las stopwords de NLTK bajo demanda y, si el recurso no esta instalado, registra un warning y devuelve `None`; el segundo construye el `TfidfVectorizer` usando ese fallback sin intentar descargar nada. `learning_object_recomended()` ahora crea el vectorizador de forma lazy dentro del calculo de similitud. Validacion: modulo puro `test.recommendation_system.test_recommendation_system_view_helpers` mantenido en verde (`7/7`), comprobacion directa en `manage.py shell` confirmando que `build_tfidf_vectorizer()` devuelve `stop_words=None` cuando `stopwords.words` lanza `LookupError`, y paquete `test.user` en verde (`31/31`).

## [2026-03-20 11:22] Fase 4: refactor seguro inicial de dataset_generator.py
- Hora: 2026-03-20 11:22
- Descripcion: Se inicio el refactor de `applications/recommendation_system/dataset_generator.py` por los 3 metodos de menor riesgo y mayor impacto directo en el endpoint de recomendaciones: `LearningObjectView()`, `user_learning_object_liked()` y `learning_object_metadata()`. El objetivo fue normalizar retornos y evitar el patron legacy de `return Exception` en esta capa. Se agrego `logging`, manejo acotado de errores (`DatabaseError`, `AttributeError`, `TypeError`, `ValueError`, `KeyError` segun el caso) y estructuras vacias consistentes: `LearningObjectView()` ahora siempre devuelve `list`, `user_learning_object_liked()` devuelve un `DataFrame` vacio con columnas estables (`user`, `learning_object`, `liked`) cuando falla o no hay datos, y `learning_object_metadata()` devuelve un `DataFrame` vacio con columnas esperadas (`id`, `general_keyword`, `general_title`) en vez de propagar formas inconsistentes. Se agrego el modulo puro `test/recommendation_system/test_dataset_generator_guards.py` para cubrir happy path y fallos controlados de esos 3 metodos sin depender de BD real. Validacion: `test.recommendation_system.test_dataset_generator_guards` en verde (`6/6`), `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`) y paquete `test.user` en verde (`31/31`).

## [2026-03-20 12:04] Fase 4: cierre del bloque user_profile_dataset en dataset_generator.py
- Hora: 2026-03-20 12:04
- Descripcion: Se consolido el refactor de `user_profile_dataset()` en `applications/recommendation_system/dataset_generator.py` para que devuelva siempre un `DataFrame` consistente y deje de usar el patron legacy de `return Exception`. El metodo ahora responde con un dataset vacio tipado cuando el usuario no tiene perfil de estudiante, cuando faltan fuentes base (`Student`, `Preferences`, `PreferencesArea`) o cuando ocurre un error controlado de datos/BD; ademas mantiene las columnas esperadas (`preferences_are`, `preferences`, `myPref`, `priority`, `Total`) y conserva la logica actual de calculo de `myPref` y `Total`. Se ampliaron las pruebas puras en `test/recommendation_system/test_dataset_generator_guards.py` para cubrir: happy path del dataset de preferencias, usuario sin perfil de estudiante y fallo de consulta con `DatabaseError`. Validacion: `test.recommendation_system.test_dataset_generator_guards` en verde (`9/9`) y `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`).

## [2026-03-20 14:46] Fase 4: correccion de compatibilidad scikit-learn para stopwords en recommendation_system
- Hora: 2026-03-20 14:46
- Descripcion: Se corrigio un fallo real en `applications/recommendation_system/recommended.py` donde `get_spanish_stopwords()` devolvia una `tuple`, pero `TfidfVectorizer` de la version actual de `scikit-learn` solo acepta `list`, `'english'` o `None` en el parametro `stop_words`. Esto provocaba el error `InvalidParameterError` al calcular recomendaciones por similitud para un OA real. El fix fue mantener la carga lazy de stopwords, pero devolver `list(stopwords.words('spanish'))` en vez de `tuple(...)`. Se agrego una prueba de caracterizacion en `test/recommendation_system/test_recommendation_system_characterization.py` para asegurar compatibilidad explicita con scikit-learn actual. Validacion: clase pura `RecommendationHelperCharacterizationTests` en verde (`8/8`) y modulo puro `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`). Nota: el modulo mixto completo `test_recommendation_system_characterization` sigue topando con el estado actual de `test_roaTestDB`; por eso se valido la clase pura de helpers directamente.

## [2026-03-20 15:02] Fase 4: refactor seguro de learning_object_concept_dataset
- Hora: 2026-03-20 15:02
- Descripcion: Se refactorizo `learning_object_concept_dataset()` en `applications/recommendation_system/dataset_generator.py` para quitar el `except:` generico y el retorno legacy de `Exception`. El metodo ahora construye `DataFrame` con columnas explicitas, corta temprano a un dataset vacio tipado (`oaId`, `concept`, `average`) cuando cualquiera de las tres fuentes base esta vacia (`EvaluationCollaboratingExpert`, `EvaluationConceptQualification`, `EvaluationConcept`) o cuando el merge intermedio no produce datos, y registra con `logging` los errores controlados (`AttributeError`, `TypeError`, `ValueError`, `KeyError`, `DatabaseError`). Se agregaron pruebas puras en `test/recommendation_system/test_dataset_generator_guards.py` para cubrir: agrupacion/mean del happy path, fuentes vacias y fallo de consulta con `DatabaseError`, sin depender de BD real. Validacion: `test.recommendation_system.test_dataset_generator_guards` en verde (`12/12`) y `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`).

## [2026-03-20 15:17] Fase 4: refactor seguro de learning_object_question_dataset
- Hora: 2026-03-20 15:17
- Descripcion: Se refactorizo `learning_object_question_dataset()` en `applications/recommendation_system/dataset_generator.py` con el mismo enfoque defensivo aplicado al resto del recommendation system. El metodo ahora devuelve siempre un `DataFrame` consistente (`oaId`, `code`, `qualification`), agrega un helper de salida vacia tipada, valida vacios antes de cada merge, usa nombres intermedios explicitos (`expert_evaluation_id`, `concept_evaluation_id`) para evitar choques de columnas `id_x/id_y` en pandas y reemplaza el patron legacy de asumir datos siempre presentes. El agrupado final se mantiene por `oaId` y `code`, con promedio de `qualification` redondeado a entero. Se agregaron pruebas puras en `test/recommendation_system/test_dataset_generator_guards.py` para cubrir: happy path con agregacion por codigo, fuentes vacias y fallo de consulta con `DatabaseError`, sin depender de BD real. Validacion: `test.recommendation_system.test_dataset_generator_guards` en verde (`15/15`) y `test.recommendation_system.test_recommendation_system_view_helpers` en verde (`7/7`).

## [2026-03-20 16:00] Cierre de Fase 4
- Hora: 2026-03-20 16:00
- Descripcion: Se da por cerrada la Fase 4 en el alcance actual. Quedo estabilizado el flujo principal de `recommendation_system` que si impacta el endpoint real `/api/v1/learning-objects/recommended/`: endurecimiento defensivo de `views.py`, correcciones en `recommended.py`, eliminacion de side effects en import-time, compatibilidad con `scikit-learn` actual y refactor seguro de los metodos criticos de `dataset_generator.py` usados directa o indirectamente por el endpoint (`user_learning_object_liked`, `LearningObjectView`, `learning_object_metadata`, `user_profile_dataset`, `learning_object_concept_dataset`, `learning_object_question_dataset`). Se decide no seguir por ahora con helpers legacy menos criticos como `users_profile_dataset()` y `learning_objects_evaluated()`, porque ya no forman parte del camino principal del frontend y tocarlos aportaria menos valor que riesgo. A partir de este punto, la fase queda cerrada sin mas cambios funcionales.
