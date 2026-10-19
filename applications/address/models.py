"""App sin modelos activos.

Los catalogos de pais, provincia, ciudad, universidad y campus se eliminaron:
la ubicacion del usuario se guarda como texto en `user.User` y el frontend la
toma de un catalogo geografico externo. La app sigue registrada en
`INSTALLED_APPS` solo para conservar su historial de migraciones, que es el que
elimina las tablas en las bases existentes.
"""
