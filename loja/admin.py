from django.contrib import admin
from .models import Categoria, Produto, Pedido, ItemPedido

admin.site.register([Categoria, Produto, Pedido, ItemPedido])