"""Rutas manuales del módulo de interacciones.

Este archivo agrupa endpoints que no salen del router principal, sobre todo:

- consulta del estado liked de un OA para el usuario actual
- creación y consulta de contadores de descargas y vistas
- rankings públicos de likes
- generación del token auxiliar `interaction-ref`

Varias rutas se publican con y sin slash final para conservar compatibilidad
con clientes legacy del frontend.
"""

from rest_framework.routers import DefaultRouter

from django.contrib import admin
from django.urls import path
from . import views

# Alias locales para mantener legible el bloque de rutas sin repetir `as_view()`.
liked_detail_view = views.GetLikedLearningObjetById.as_view()
download_create_view = views.CreateDownload.as_view()
download_detail_view = views.GetUpdateDownloadNumber.as_view()
view_create_view = views.CreateViewInteraction.as_view()
view_detail_view = views.GetUpdateViewNumberView.as_view()
interaction_ref_view = views.UserRefTokenInteraction.as_view()
interaction_ref_legacy_view = views.UserRefTokenInteractionLegacy.as_view()
most_liked_view = views.MostLikeLearningObjects.as_view()
liked_count_view = views.LearingObjectLike.as_view()


app_name = 'intearaction'
urlpatterns = [
    # Estado de like del usuario autenticado para un OA concreto.
    path('api/v1/learning-objects/liked/<int:pk>', liked_detail_view, name='interaction-liked-legacy'),

    # Registro inicial y consulta/incremento del contador de descargas.
    path('api/v1/learning-objects/downloaded', download_create_view),
    path('api/v1/learning-objects/downloaded/<int:pk>', download_detail_view),

    # Registro inicial y consulta/actualización del contador agregado de vistas.
    path('api/v1/learning-objects/viewed', view_create_view),
    path('api/v1/learning-objects/viewed/<int:pk>', view_detail_view),

    # Token auxiliar protegido por clave compartida para el flujo interaction-ref.
    path('api/v1/interaction-ref/', interaction_ref_view),

    # Rankings públicos y conteo agregado de likes por OA.
    path('api/v1/learning-objects/most-liked/', most_liked_view),
    path('api/v1/learning-objects/liked-count/<int:pk>', liked_count_view),
]
