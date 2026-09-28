# Test Suite Structure

This folder contains test modules organized by backend app.

## Run only user/authentication tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.user.authentication --verbosity 3
```

## Run full upload flow test (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_file.test_full_upload_flow --verbosity 3
```

## Run upload error cases for learning object file (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_file.test_upload_error_cases --verbosity 3
```

Notes:
- Provide a real OA ZIP in `test/fixtures/oa_real_test.zip`, or set:

```powershell
$env:TEST_REAL_OA_ZIP_PATH='C:\ruta\tu-oa-real.zip'
```

## Run student and expert evaluation tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.evaluation_student.test_student_evaluation_flow test.evaluation_collaborating_expert.test_expert_evaluation_flow --verbosity 3
```

## Run only expert evaluation tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.evaluation_collaborating_expert.test_expert_evaluation_flow --verbosity 3
```

## Run metadata automatic/manual evaluation tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_metadata.test_metadata_evaluation_thresholds --verbosity 3
```

## Run role permission matrix tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.user.permissions.test_role_permission_matrix --verbosity 3
```

## Run admin CRUD tests for concepts/questions/guidelines (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.evaluation_collaborating_expert.test_admin_crud_concepts_questions test.evaluation_student.test_admin_crud_principles_guidelines_questions --verbosity 3
```

## Run education level full tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.education_level.test_education_level_full --verbosity 3
```

## Run knowledge area full tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.knowledge_area.test_knowledge_area_full --verbosity 3
```

## Run address full tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.address.test_address_full --verbosity 3
```

## Run license full tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.license.test_license_full --verbosity 3
```

## Run profession full tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.profession.test_profession_full --verbosity 3
```

## Run public OA filter tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_metadata.test_public_oa_filters --verbosity 3
```

## Run settings validation serializer tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.settings.test_settings_validation_serializers --verbosity 3 --keepdb
```

## Run settings error handling tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.settings.test_settings_error_handling --verbosity 3 --keepdb
```

## Run settings URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.settings.test_settings_url_compatibility --verbosity 3 --keepdb
```

## Run user URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.user.test_user_url_compatibility --verbosity 3 --keepdb
```

## Run user env compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.user.test_user_env_compatibility --verbosity 3 --keepdb
```

## Run user management update tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.user.test_user_management_update --verbosity 3 --keepdb
```

## Run address URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.address.test_address_url_compatibility --verbosity 3 --keepdb
```

## Run preferences URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.preferences.test_preferences_url_compatibility --verbosity 3 --keepdb
```

## Run license URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.license.test_license_url_compatibility --verbosity 3 --keepdb
```

## Run learning object file OER URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_file.test_oer_url_compatibility --verbosity 3 --keepdb
```

## Run recommendation system characterization tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.recommendation_system.test_recommendation_system_characterization --verbosity 3 --keepdb
```

## Run recommendation system view helper tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.recommendation_system.test_recommendation_system_view_helpers --verbosity 3
```

## Run recommendation system dataset generator guard tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.recommendation_system.test_dataset_generator_guards --verbosity 3
```

## Run interaction validation serializer tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.interaction.test_interaction_validation_serializers --verbosity 3 --keepdb
```

## Run interaction URL compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.interaction.test_interaction_url_compatibility --verbosity 3 --keepdb
```

## Run learning object metadata mail compatibility tests (PowerShell)

```powershell
$env:DEBUG='1'; .\venv\Scripts\python.exe manage.py test test.learning_object_metadata.test_mail_metadata_error_handling --verbosity 3 --keepdb
```
