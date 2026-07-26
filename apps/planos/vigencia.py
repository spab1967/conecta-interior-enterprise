import calendar
from datetime import date


def adicionar_um_mes(data):

    if not isinstance(data, date):
        raise ValueError(
            "A data inicial da assinatura é inválida."
        )

    if data.month == 12:
        ano = data.year + 1
        mes = 1
    else:
        ano = data.year
        mes = data.month + 1

    ultimo_dia = calendar.monthrange(
        ano,
        mes,
    )[1]

    dia = min(
        data.day,
        ultimo_dia,
    )

    return date(
        ano,
        mes,
        dia,
    )


def calcular_vencimento_plano(
    plano,
    inicio,
):

    if plano is None:
        raise ValueError(
            "Plano não informado."
        )

    if inicio is None:
        raise ValueError(
            "Data inicial não informada."
        )

    if plano.preco_mensal <= 0:
        return None

    return adicionar_um_mes(
        inicio
    )