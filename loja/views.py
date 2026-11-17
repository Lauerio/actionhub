from django.views.decorators.http import require_POST
import random
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import CadastroForm
from .models import Categoria, Produto, Pedido, ItemPedido

# ---------- Avaliações simuladas ----------
NOMES = ["Lucas M.", "Ana Paula", "Rafael S.", "Beatriz L.", "Thiago R.",
         "Camila F.", "Pedro H.", "Juliana C.", "Gabriel A.", "Mariana T."]

COMENTARIOS = [
    (5, "Chegou antes do prazo e muito bem embalada. Detalhes impecáveis!"),
    (5, "Superou minhas expectativas, a pintura é muito bem feita."),
    (5, "Perfeita para a minha coleção, recomendo!"),
    (4, "Muito boa, articulações firmes. Só achei a caixa um pouco pequena."),
    (4, "Ótimo custo-benefício, valeu cada centavo."),
    (4, "Bonita e resistente, entrega rápida."),
    (3, "Boa, mas esperava um acabamento melhor na base."),
    (5, "Presente perfeito, meu filho amou!"),
]


def classes_estrelas(nota):
    """Lista de 5 ícones (cheia, meia, vazia) para desenhar as estrelas."""
    cheias = int(nota)
    meia = (nota - cheias) >= 0.5
    classes = ["bi-star-fill"] * cheias
    if meia:
        classes.append("bi-star-half")
    classes += ["bi-star"] * (5 - len(classes))
    return classes


def simular_avaliacoes(produto):
    rng = random.Random(produto.id)      # mesmo produto = mesmas avaliações
    qtd = rng.randint(4, 6)
    nomes = rng.sample(NOMES, qtd)
    textos = rng.sample(COMENTARIOS, qtd)
    base = date(2026, 11, 10)

    avaliacoes = []
    for nome, (nota, texto) in zip(nomes, textos):
        avaliacoes.append({
            "nome": nome,
            "inicial": nome[0],
            "nota": nota,
            "estrelas": classes_estrelas(nota),
            "texto": texto,
            "data": base - timedelta(days=rng.randint(3, 120)),
        })
    media = round(sum(a["nota"] for a in avaliacoes) / len(avaliacoes), 1)
    return avaliacoes, media, classes_estrelas(media)


# ---------- Views ----------
def lista(request):
    produtos = Produto.objects.all()
    cat = request.GET.get("categoria")
    if cat:
        produtos = produtos.filter(categoria_id=cat)

    produtos = list(produtos)
    for p in produtos:
        avaliacoes, p.media, p.estrelas = simular_avaliacoes(p)
        p.total_avaliacoes = len(avaliacoes)

    return render(request, "loja/lista.html", {
        "produtos": produtos,
        "categorias": Categoria.objects.all(),
    })


def detalhe(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    avaliacoes, media, estrelas = simular_avaliacoes(produto)
    relacionados = (Produto.objects.filter(categoria=produto.categoria)
                    .exclude(id=produto.id)[:4])

    return render(request, "loja/detalhe.html", {
        "produto": produto,
        "avaliacoes": avaliacoes,
        "media": media,
        "estrelas": estrelas,
        "total_avaliacoes": len(avaliacoes),
        "preco_pix": produto.preco * Decimal("0.90"),
        "parcela": produto.preco / 6,
        "frete_gratis": produto.preco >= 299,
        "relacionados": relacionados,
    })


def cadastro(request):
    form = CadastroForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("login")
    return render(request, "registration/cadastro.html", {"form": form})


@login_required
def adicionar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    pedido, _ = Pedido.objects.get_or_create(usuario=request.user, finalizado=False)
    item, criado = ItemPedido.objects.get_or_create(pedido=pedido, produto=produto)
    if not criado and item.quantidade < produto.estoque:
        item.quantidade += 1
        item.save()
    return redirect("carrinho")


@login_required
def carrinho(request):
    pedido = Pedido.objects.filter(usuario=request.user, finalizado=False).first()
    itens = list(pedido.itens.select_related("produto")) if pedido else []

    total = sum((i.subtotal for i in itens), Decimal("0"))
    faltam_frete = Decimal("299") - total

    return render(request, "loja/carrinho.html", {
        "pedido": pedido,
        "itens": itens,
        "qtd_total": sum(i.quantidade for i in itens),
        "total": total,
        "total_pix": total * Decimal("0.90"),
        "frete_gratis": total >= 299,
        "faltam_frete": faltam_frete,
        "progresso_frete": min(int(total / Decimal("299") * 100), 100) if total else 0,
    })

def _item_do_usuario(request, item_id):
    """Garante que o item é do carrinho aberto do próprio usuário."""
    return get_object_or_404(
        ItemPedido, id=item_id,
        pedido__usuario=request.user, pedido__finalizado=False,
    )


@login_required
@require_POST
def finalizar(request):
    pedido = get_object_or_404(
        Pedido,
        usuario=request.user,
        finalizado=False
    )

    if not pedido.itens.exists():
        return redirect("carrinho")

    pedido.finalizado = True
    pedido.save()

    return redirect("meus_pedidos")


@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(
        usuario=request.user,
        finalizado=True
    ).prefetch_related("itens__produto")

    return render(request, "loja/meus_pedidos.html", {
        "pedidos": pedidos
    })


@login_required
@require_POST
def aumentar(request, item_id):
    item = _item_do_usuario(request, item_id)
    if item.quantidade < item.produto.estoque:
        item.quantidade += 1
        item.save()
    return redirect("carrinho")


@login_required
@require_POST
def diminuir(request, item_id):
    item = _item_do_usuario(request, item_id)
    if item.quantidade > 1:
        item.quantidade -= 1
        item.save()
    else:
        item.delete()
    return redirect("carrinho")


@login_required
@require_POST
def remover(request, item_id):
    _item_do_usuario(request, item_id).delete()
    return redirect("carrinho")


@login_required
@require_POST
def esvaziar(request):
    ItemPedido.objects.filter(
        pedido__usuario=request.user,
        pedido__finalizado=False
    ).delete()
    return redirect("carrinho")
