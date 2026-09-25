"""Pruebas del helper de correo usado al aprobar metadata de un OA.

Estas pruebas no validan SMTP real. Se concentran en dos comportamientos
esperados del helper:
- si falla la lectura de la plantilla, el error debe quedar logueado sin
  romper el flujo llamador
- si falta `DOMAIN_HOST_ROA`, el helper debe degradar a `DOMAIN_HOST`

La idea es proteger fallos operativos comunes sin depender de red ni de una
configuración real de correo.
"""

import os
from unittest.mock import mock_open, patch

from django.test import SimpleTestCase

from applications.learning_object_metadata.testMailMetadata import SendEmailCreateOA_satisfay


class LearningObjectMetadataMailErrorHandlingTests(SimpleTestCase):
    """Cubre fallos recuperables del mailer de metadata de objetos de aprendizaje."""

    def test_send_mail_create_oa_swallow_oserror_and_logs(self):
        """Registra el error y no propaga la excepción si falla la plantilla.

        Este caso protege al flujo de aprobación del OA frente a errores de
        filesystem o plantillas faltantes. El correo puede fallar, pero la
        aplicación no debe caerse por eso.
        """
        with patch("builtins.open", side_effect=OSError("template missing")):
            with self.assertLogs("applications.learning_object_metadata.testMailMetadata", level="ERROR") as captured:
                SendEmailCreateOA_satisfay().sendMailCreateOA(
                    "test@example.com",
                    "Administrador",
                    "OA Demo",
                )

        self.assertTrue(
            any("Error enviando correo de OA satisfactorio para administrador" in message for message in captured.output)
        )

    def test_send_mail_create_oa_falls_back_to_domain_host_when_roa_host_is_missing(self):
        """Usa `DOMAIN_HOST` como fallback cuando falta `DOMAIN_HOST_ROA`.

        El helper históricamente construye enlaces con dos variables de
        entorno. Esta prueba deja claro cuál es el comportamiento esperado si
        la variable más específica no existe.
        """
        with patch.dict(os.environ, {"DOMAIN_HOST": "http://fallback.local"}, clear=False):
            os.environ.pop("DOMAIN_HOST_ROA", None)
            with patch("builtins.open", mock_open(read_data="Portal {HOST}")):
                with patch("applications.learning_object_metadata.testMailMetadata.MIMEText") as mock_mime_text:
                    with patch(
                        "applications.learning_object_metadata.testMailMetadata.threading.Thread.start"
                    ) as mock_thread_start:
                        SendEmailCreateOA_satisfay().sendMailCreateOA(
                            "test@example.com",
                            "Administrador",
                            "OA Demo",
                        )

        payload = mock_mime_text.call_args[0][0]
        self.assertIn(b"http://fallback.local", payload)
        mock_thread_start.assert_called_once()
