from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista, name="lista"),
    path("produto/<int:produto_id>/", views.detalhe, name="detalhe"),
    path("cadastro/", views.cadastro, name="cadastro"),
    path("adicionar/<int:produto_id>/", views.adicionar, name="adicionar"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path("carrinho/aumentar/<int:item_id>/", views.aumentar, name="aumentar"),
    path("carrinho/diminuir/<int:item_id>/", views.diminuir, name="diminuir"),
    path("carrinho/remover/<int:item_id>/", views.remover, name="remover"),
    path("carrinho/esvaziar/", views.esvaziar, name="esvaziar"),
    path("finalizar/", views.finalizar, name="finalizar"),
    path("meus-pedidos/", views.meus_pedidos, name="meus_pedidos"),
]