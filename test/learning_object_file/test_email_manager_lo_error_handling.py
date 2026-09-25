"""Pruebas de manejo seguro de errores en `emailManagerLO`.

Este archivo cubre un caso pequeño pero importante: que un fallo recuperable al
construir o enviar el correo de eliminación no haga caer el flujo completo y
quede al menos registrado en logs.
"""

from unittest.mock import patch

from django.test import SimpleTestCase

from applications.learning_object_file.emailManagerLO import SendMail


class LearningObjectFileEmailManagerErrorHandlingTests(SimpleTestCase):
    """Verifica que errores recuperables del mailer no rompan el flujo."""

    def test_send_mail_delete_oa_swallow_oserror_and_logs(self):
        """Comprueba que un `OSError` se registre y no se propague.

        El caso simula una plantilla ausente y verifica que el helper mantenga
        el comportamiento tolerante a fallos esperado por el resto del sistema.
        """
        with patch("builtins.open", side_effect=OSError("template missing")):
            with self.assertLogs("applications.learning_object_file.emailManagerLO", level="ERROR") as captured:
                SendMail().sendMailDeleteOA(
                    "test@example.com",
                    "Usuario",
                    "OA Demo",
                    "Motivo de eliminacion",
                )

        self.assertTrue(
            any("Error al enviar el correo de eliminacion de OA" in message for message in captured.output)
        )
