"""Pruebas del comando que limpia paquetes OA huerfanos."""

import os
import shutil
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from applications.education_level.models import EducationLevel
from applications.knowledge_area.models import KnowledgeArea
from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata
from applications.license.models import License
from test.helpers.temp_media_root import build_test_media_root


class CleanupOrphanLearningObjectFilesCommandTests(TestCase):
    """Cubre la limpieza diferida de ZIPs y carpetas extraidas sin metadata."""

    def setUp(self):
        self.media_root = build_test_media_root("test-media-cleanup-orphans-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_learning_object_file(self, name, age_hours=48, path_origin=None):
        upload = SimpleUploadedFile(
            f"{name}.zip",
            b"zip-content",
            content_type="application/zip",
        )
        learning_object_file = LearningObjectFile.objects.create(
            file=upload,
            url=f"http://testserver/media/catalog/{name}/index.html",
            file_name=name,
            file_size=11,
        )
        catalog_path = Path(path_origin or Path(self.media_root) / "catalog" / name)
        catalog_path.mkdir(parents=True, exist_ok=True)
        (catalog_path / "index.html").write_text("content", encoding="utf-8")

        learning_object_file.path_origin = str(catalog_path)
        learning_object_file.save(update_fields=["path_origin"])

        created = timezone.now() - timedelta(hours=age_hours)
        LearningObjectFile.objects.filter(pk=learning_object_file.pk).update(
            created=created,
            modified=created,
        )
        learning_object_file.refresh_from_db()
        return learning_object_file, Path(learning_object_file.file.path), catalog_path

    def _set_old_mtime(self, path, age_hours=48):
        old_timestamp = (timezone.now() - timedelta(hours=age_hours)).timestamp()
        os.utime(path, (old_timestamp, old_timestamp))

    def _create_physical_orphans(self, name, age_hours=48):
        oazip_root = Path(self.media_root) / "oazip"
        catalog_root = Path(self.media_root) / "catalog"
        oazip_root.mkdir(parents=True, exist_ok=True)
        catalog_root.mkdir(parents=True, exist_ok=True)

        zip_path = oazip_root / f"{name}.zip"
        zip_path.write_bytes(b"orphan-zip")
        catalog_path = catalog_root / name
        catalog_path.mkdir(parents=True, exist_ok=True)
        (catalog_path / "index.html").write_text("content", encoding="utf-8")

        self._set_old_mtime(zip_path, age_hours)
        self._set_old_mtime(catalog_path / "index.html", age_hours)
        self._set_old_mtime(catalog_path, age_hours)
        return zip_path, catalog_path

    def _create_model_file_orphan(self, folder, filename, age_hours=48):
        root = Path(self.media_root) / folder
        root.mkdir(parents=True, exist_ok=True)
        file_path = root / filename
        file_path.write_bytes(b"orphan-file")
        self._set_old_mtime(file_path, age_hours)
        return file_path

    def _create_metadata_for(self, learning_object_file):
        education_level = EducationLevel.objects.create(
            name_es="Nivel Cleanup",
            name_en="Cleanup Level",
        )
        knowledge_area = KnowledgeArea.objects.create(
            name_es="Area Cleanup",
            description_es="Desc",
            name_en="Cleanup Area",
            description_en="Desc",
        )
        license_obj = License.objects.create(
            name_es="Licencia Cleanup",
            name_en="Cleanup License",
            value="CLEANUP",
        )
        return LearningObjectMetadata.objects.create(
            learning_object_file=learning_object_file,
            adaptation="N",
            avatar=SimpleUploadedFile(
                "avatar.png",
                b"avatar",
                content_type="image/png",
            ),
            general_title="OA Cleanup",
            general_language="es",
            education_levels=education_level,
            knowledge_area=knowledge_area,
            license=license_obj,
        )

    def _run_command(self, *args):
        stdout = StringIO()
        stderr = StringIO()
        call_command(
            "cleanup_orphan_learning_object_files",
            *args,
            stdout=stdout,
            stderr=stderr,
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_deletes_old_orphan_zip_catalog_and_record(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "old-orphan",
            age_hours=48,
        )

        stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("deleted=1", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertFalse(zip_path.exists())
        self.assertFalse(catalog_path.exists())

    def test_dry_run_reports_without_deleting(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "dry-run-orphan",
            age_hours=48,
        )

        stdout, stderr = self._run_command("--hours", "24", "--dry-run")

        self.assertIn("[dry-run]", stdout)
        self.assertIn("deleted=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_keeps_recent_orphan(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "recent-orphan",
            age_hours=1,
        )

        stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("found=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_keeps_old_file_with_metadata(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "with-metadata",
            age_hours=48,
        )
        self._create_metadata_for(learning_object_file)

        stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("found=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_skips_unsafe_catalog_path(self):
        unsafe_path = Path(self.media_root).parent / "unsafe-catalog-cleanup"
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "unsafe-orphan",
            age_hours=48,
            path_origin=unsafe_path,
        )

        stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("unsafe path", stdout)
        self.assertIn("deleted=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())
        shutil.rmtree(unsafe_path, ignore_errors=True)

    def test_missing_physical_files_still_remove_old_orphan_record(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "missing-files-orphan",
            age_hours=48,
        )
        os.remove(zip_path)
        shutil.rmtree(catalog_path)

        stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("deleted=1", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())

    def test_revalidates_metadata_before_delete(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "race-condition",
            age_hours=48,
        )

        original_has_metadata = (
            "applications.learning_object_file.management.commands."
            "cleanup_orphan_learning_object_files.Command._has_metadata"
        )
        with patch(original_has_metadata, return_value=True):
            stdout, stderr = self._run_command("--hours", "24")

        self.assertIn("metadata exists", stdout)
        self.assertIn("deleted=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_deletes_old_physical_zip_and_catalog_without_database_record(self):
        zip_path, catalog_path = self._create_physical_orphans(
            "physical-orphan",
            age_hours=48,
        )

        stdout, stderr = self._run_command("--hours", "24", "--include-physical-orphans")

        self.assertIn("Physical orphan cleanup summary", stdout)
        self.assertIn("deleted=2", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(zip_path.exists())
        self.assertFalse(catalog_path.exists())

    def test_dry_run_keeps_physical_orphans(self):
        zip_path, catalog_path = self._create_physical_orphans(
            "physical-dry-run",
            age_hours=48,
        )

        stdout, stderr = self._run_command(
            "--hours",
            "24",
            "--include-physical-orphans",
            "--dry-run",
        )

        self.assertIn("[dry-run] physical orphan ZIP", stdout)
        self.assertIn("[dry-run] physical orphan catalog", stdout)
        self.assertIn("deleted=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_keeps_recent_physical_orphans(self):
        zip_path, catalog_path = self._create_physical_orphans(
            "physical-recent",
            age_hours=1,
        )

        stdout, stderr = self._run_command("--hours", "24", "--include-physical-orphans")

        self.assertIn("Physical orphan cleanup summary", stdout)
        self.assertIn("found=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_keeps_physical_paths_referenced_by_database(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "referenced-physical",
            age_hours=48,
        )
        self._create_metadata_for(learning_object_file)
        self._set_old_mtime(zip_path, 48)
        self._set_old_mtime(catalog_path, 48)

        stdout, stderr = self._run_command("--hours", "24", "--include-physical-orphans")

        self.assertIn("Physical orphan cleanup summary", stdout)
        self.assertIn("found=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_keeps_catalog_referenced_only_by_url(self):
        learning_object_file, zip_path, catalog_path = self._create_learning_object_file(
            "url-referenced-catalog",
            age_hours=48,
        )
        self._create_metadata_for(learning_object_file)
        LearningObjectFile.objects.filter(pk=learning_object_file.pk).update(
            path_origin="",
            url="http://testserver/media/catalog/url-referenced-catalog/index.html",
        )
        self._set_old_mtime(zip_path, 48)
        self._set_old_mtime(catalog_path, 48)

        stdout, stderr = self._run_command("--hours", "24", "--include-physical-orphans")

        self.assertIn("Physical orphan cleanup summary", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(LearningObjectFile.objects.filter(pk=learning_object_file.pk).exists())
        self.assertTrue(zip_path.exists())
        self.assertTrue(catalog_path.exists())

    def test_deletes_old_model_file_orphans(self):
        avatar_path = self._create_model_file_orphan("avatar", "orphan-avatar.png")
        source_path = self._create_model_file_orphan("sourceFile", "orphan-source.zip")
        profile_path = self._create_model_file_orphan("profile", "orphan-profile.png")

        stdout, stderr = self._run_command("--hours", "24", "--include-model-file-orphans")

        self.assertIn("Model file orphan cleanup summary", stdout)
        self.assertIn("deleted=3", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(avatar_path.exists())
        self.assertFalse(source_path.exists())
        self.assertFalse(profile_path.exists())

    def test_dry_run_keeps_model_file_orphans(self):
        avatar_path = self._create_model_file_orphan("avatar", "dry-avatar.png")
        source_path = self._create_model_file_orphan("sourceFile", "dry-source.zip")
        profile_path = self._create_model_file_orphan("profile", "dry-profile.png")

        stdout, stderr = self._run_command(
            "--hours",
            "24",
            "--include-model-file-orphans",
            "--dry-run",
        )

        self.assertIn("[dry-run] model file orphan avatar", stdout)
        self.assertIn("[dry-run] model file orphan sourceFile", stdout)
        self.assertIn("[dry-run] model file orphan profile", stdout)
        self.assertIn("deleted=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(avatar_path.exists())
        self.assertTrue(source_path.exists())
        self.assertTrue(profile_path.exists())

    def test_keeps_model_files_referenced_by_database(self):
        learning_object_file, _, _ = self._create_learning_object_file(
            "referenced-model-files",
            age_hours=48,
        )
        metadata = self._create_metadata_for(learning_object_file)
        metadata.source_file = SimpleUploadedFile(
            "referenced-source.zip",
            b"source",
            content_type="application/zip",
        )
        metadata.save(update_fields=["source_file"])

        user = get_user_model().objects.create_user(
            email="cleanup-user@test.com",
            first_name="Cleanup",
            last_name="User",
            password="testpass123",
        )
        user.image = SimpleUploadedFile(
            "referenced-profile.png",
            b"profile",
            content_type="image/png",
        )
        user.save(update_fields=["image"])

        avatar_path = Path(metadata.avatar.path)
        source_path = Path(metadata.source_file.path)
        profile_path = Path(user.image.path)
        self._set_old_mtime(avatar_path, 48)
        self._set_old_mtime(source_path, 48)
        self._set_old_mtime(profile_path, 48)

        stdout, stderr = self._run_command("--hours", "24", "--include-model-file-orphans")

        self.assertIn("Model file orphan cleanup summary", stdout)
        self.assertIn("found=0", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(avatar_path.exists())
        self.assertTrue(source_path.exists())
        self.assertTrue(profile_path.exists())
