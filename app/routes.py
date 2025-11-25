from flask import Blueprint, render_template, request

from .config import Config
from .services import (
    AtividadeMEI,
    ATIVIDADE_LABELS,
    calcular_situacao_mei,
)

main_bp = Blueprint("main", __name__)


def _parse_faturamento(value: str) -> float:
    value = (value or "").strip()
    if not value:
        return 0.0
    # aceita 35.000,00 ou 35000,00
    value = value.replace(".", "").replace(",", ".")
    return float(value)


def _parse_meses(value: str) -> int:
    try:
        m = int((value or "12").strip())
    except ValueError:
        m = 12
    return max(1, min(m, 12))


@main_bp.route("/", methods=["GET", "POST"])
def index():
    config = Config()
    resultado = None
    errors: dict[str, str] = {}

    dados_form = {
        "faturamento_anual": "",
        "meses_atividade": "12",
        "atividade": AtividadeMEI.COMERCIO_INDUSTRIA.value,
    }

    if request.method == "POST":
        faturamento_raw = request.form.get("faturamento_anual", "")
        meses_raw = request.form.get("meses_atividade", "12")
        atividade_raw = request.form.get("atividade", AtividadeMEI.COMERCIO_INDUSTRIA.value)

        dados_form["faturamento_anual"] = faturamento_raw
        dados_form["meses_atividade"] = meses_raw
        dados_form["atividade"] = atividade_raw

        # Faturamento
        try:
            faturamento_anual = _parse_faturamento(faturamento_raw)
            if faturamento_anual < 0:
                raise ValueError
        except ValueError:
            errors["faturamento_anual"] = "Informe um valor numérico válido."
            faturamento_anual = 0.0

        # Meses
        try:
            meses_atividade = _parse_meses(meses_raw)
        except ValueError:
            errors["meses_atividade"] = "Informe um número entre 1 e 12."
            meses_atividade = 12

        # Atividade
        try:
            atividade = AtividadeMEI(atividade_raw)
        except ValueError:
            atividade = AtividadeMEI.COMERCIO_INDUSTRIA

        if not errors:
            resultado = calcular_situacao_mei(
                faturamento_anual=faturamento_anual,
                meses_atividade=meses_atividade,
                atividade=atividade,
                config=config,
            )

    return render_template(
        "index.html",
        config=config,
        dados_form=dados_form,
        errors=errors,
        resultado=resultado,
        atividades=AtividadeMEI,
        atividade_labels=ATIVIDADE_LABELS,
    )


@main_bp.route("/relatorio")
def relatorio():
    """Gera uma página limpa para impressão / salvar em PDF (via navegador)."""

    config = Config()

    faturamento_raw = request.args.get("faturamento_anual", "")
    meses_raw = request.args.get("meses_atividade", "12")
    atividade_raw = request.args.get("atividade", AtividadeMEI.COMERCIO_INDUSTRIA.value)

    try:
        faturamento_anual = _parse_faturamento(faturamento_raw)
        meses_atividade = _parse_meses(meses_raw)
        atividade = AtividadeMEI(atividade_raw)
    except Exception:
        # se algo der errado, volta para home
        return render_template(
            "relatorio.html",
            resultado=None,
            config=config,
        )

    resultado = calcular_situacao_mei(
        faturamento_anual=faturamento_anual,
        meses_atividade=meses_atividade,
        atividade=atividade,
        config=config,
    )

    return render_template(
        "relatorio.html",
        resultado=resultado,
        config=config,
    )
