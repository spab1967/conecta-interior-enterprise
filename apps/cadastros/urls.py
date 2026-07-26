from django.urls import path

from . import views


app_name = "cadastros"


urlpatterns = [

    path(
        "",
        views.anuncie,
        name="anuncie",
    ),

    path(
        "sucesso/",
        views.sucesso,
        name="sucesso",
    ),

]