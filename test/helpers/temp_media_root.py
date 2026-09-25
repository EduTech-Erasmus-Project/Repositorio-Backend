"""Helpers para crear `MEDIA_ROOT` temporales para pruebas.

Varias suites necesitan escribir archivos reales sin contaminar `media/`.
La versión original usaba una carpeta fija dentro del repositorio, pero en
Windows ese directorio puede quedar bloqueado y romper muchas suites a la vez.
Por eso se delega la creación al directorio temporal del sistema.
"""

import tempfile


def build_test_media_root(prefix):
    """Crea un `MEDIA_ROOT` temporal y único usando el directorio temporal.

    El `prefix` ayuda a identificar qué suite creó el directorio. `mkdtemp`
    devuelve una ruta ya creada y evita colisiones entre ejecuciones repetidas.
    """
    return tempfile.mkdtemp(prefix=prefix)
