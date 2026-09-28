"""Backends de almacenamiento usados por el proyecto.

Este archivo encapsula la configuración de rutas base sobre S3-compatible
storage para separar recursos estáticos y archivos media del proyecto.
Se mantiene pequeño a propósito: la intención principal es centralizar el
contrato de almacenamiento sin duplicar configuración en múltiples puntos.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Backend para archivos estáticos recolectados por Django.

    Se publica bajo el prefijo `static/` para mantener separados los assets
    versionables del contenido subido por usuarios.
    """

    location = 'static'
    # Se usa ACL por defecto del bucket/proveedor para evitar mezclar permisos
    # a nivel de objeto desde Django.
    default_acl = None


class PublicMediaStorage(S3Boto3Storage):
    """Backend para archivos media generados o cargados por la aplicación.

    Se publica bajo el prefijo `media/` para conservar separado el contenido
    operativo del proyecto respecto a los assets estáticos.
    """

    location = 'media'
    # Se delega el control de acceso al bucket/proveedor configurado.
    default_acl = None
