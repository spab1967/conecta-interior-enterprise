from django import template

register = template.Library()


@register.filter
def estrelas(nota):
    """
    Converte uma nota de 0 a 5 em estrelas visuais.

    Exemplos:
    5 -> ★★★★★
    4 -> ★★★★☆
    3 -> ★★★☆☆
    2 -> ★★☆☆☆
    1 -> ★☆☆☆☆
    0 -> ☆☆☆☆☆
    """

    try:
        nota = float(nota or 0)
    except (TypeError, ValueError):
        nota = 0

    nota = max(0, min(5, nota))

    preenchidas = int(round(nota))

    vazias = 5 - preenchidas

    return ("★" * preenchidas) + ("☆" * vazias)