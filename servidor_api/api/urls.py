from django.urls import path

from api import views

urlpatterns = [
    path("", views.indice, name="api_indice"),
    path("sesion/", views.iniciar_sesion, name="api_sesion"),
    path("<slug:modulo>/<slug:operacion>/", views.ejecutar, name="api_ejecutar"),
]
