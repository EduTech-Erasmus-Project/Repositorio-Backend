"""Pruebas del comando que migra URLs de OAs de HTTP a HTTPS."""

import shutil
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase, override_settings

from applications.learning_object_file.models import LearningObjectFile
from test.helpers.temp_media_root import build_test_media_root


HOST = "repositorio.edutech-project.org"


class UpgradeLearningObjectUrlsToHttpsCommandTests(TestCase):
    """Cubre la correccion de URLs guardadas con esquema inseguro."""

    def setUp(self):
        self.media_root = build_test_media_root("test-media-upgrade-https-")
        self.override_media = override_settings(MEDIA_ROOT=self.media_root)
        self.override_media.enable()

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create(self, url):
        return LearningObjectFile.objects.create(
            file=SimpleUploadedFile("oa.zip", b"zip", content_type="application/zip"),
            url=url,
            file_name="oa",
            file_size=3,
        )

    def _run(self, *args):
        out = StringIO()
        call_command("upgrade_learning_object_urls_to_https", "--host", HOST, *args, stdout=out)
        return out.getvalue()

    def test_actualiza_solo_urls_http_del_host_indicado(self):
        insecure = self._create(f"http://{HOST}/media/catalog/OA/website_index.html")
        secure = self._create(f"https://{HOST}/media/catalog/OA2/index.html")
        other_host = self._create("http://otro.example.org/media/catalog/OA3/index.html")
        lookalike = self._create(f"http://{HOST}.evil.org/media/catalog/OA4/index.html")

        output = self._run()

        insecure.refresh_from_db()
        secure.refresh_from_db()
        other_host.refresh_from_db()
        lookalike.refresh_from_db()
        self.assertEqual(insecure.url, f"https://{HOST}/media/catalog/OA/website_index.html")
        self.assertEqual(secure.url, f"https://{HOST}/media/catalog/OA2/index.html")
        self.assertEqual(other_host.url, "http://otro.example.org/media/catalog/OA3/index.html")
        self.assertEqual(lookalike.url, f"http://{HOST}.evil.org/media/catalog/OA4/index.html")
        self.assertIn("Updated 1 learning object URL(s).", output)

    def test_dry_run_no_modifica_la_base(self):
        insecure = self._create(f"http://{HOST}/media/catalog/OA/index.html")

        output = self._run("--dry-run")

        insecure.refresh_from_db()
        self.assertEqual(insecure.url, f"http://{HOST}/media/catalog/OA/index.html")
        self.assertIn("Would update 1 learning object URL(s).", output)

    def test_rechaza_host_con_esquema(self):
        with self.assertRaises(CommandError):
            call_command("upgrade_learning_object_urls_to_https", "--host", f"https://{HOST}")


class SecureProxyHeaderTests(TestCase):
    """Verifica que Django respete el esquema reenviado por el proxy HTTPS."""

    def test_request_con_x_forwarded_proto_https_es_seguro(self):
        # nginx reenvia `Host $http_host`, por eso se simula `HTTP_HOST`.
        request = RequestFactory().get(
            "/", HTTP_HOST=HOST, HTTP_X_FORWARDED_PROTO="https"
        )
        with override_settings(ALLOWED_HOSTS=[HOST]):
            self.assertEqual(request.scheme, "https")
            self.assertEqual(request._current_scheme_host, f"https://{HOST}")
