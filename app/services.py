from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .config import Config


class AtividadeMEI(str, Enum):
    """
    Grupos de atividade do MEI relevantes para cálculo do DAS.

    Observação importante:
    Mesmo existindo muitos CNAEs, para efeito de DAS o MEI é
    enquadrado basicamente nesses grupos.
    """
    COMERCIO_INDUSTRIA = "comercio_industria"
    SERVICOS = "servicos"
    COMERCIO_SERVICOS = "comercio_servicos"
    CAMINHONEIRO = "caminhoneiro"


# Rótulos amigáveis para exibir nos templates
ATIVIDADE_LABELS = {
    AtividadeMEI.COMERCIO_INDUSTRIA: "Comércio / Indústria",
    AtividadeMEI.SERVICOS: "Serviços",
    AtividadeMEI.COMERCIO_SERVICOS: "Comércio + Serviços",
    AtividadeMEI.CAMINHONEIRO: "MEI Caminhoneiro",
}


# 🔹 NOVO: “mini base de conhecimento” com exemplos de cada grupo
# Isso vai nos ajudar a sugerir automaticamente o grupo
ATIVIDADE_KEYWORDS = {
    AtividadeMEI.SERVICOS: [
        # motoristas / entrega
        "uber", "99", "ifood", "i food", "entregador", "delivery",
        "motoboy", "moto boy", "motorista",
        # construção / manutenção
        "pedreiro", "pintor", "marceneiro", "eletricista", "gesso", "reforma",
        # tecnologia / criação
        "programador", "desenvolvedor", "dev", "designer", "social media",
        "marketing", "fotografo", "fotógrafo",
        # beleza / cuidados pessoais
        "manicure", "barbeiro", "cabeleireiro", "maquiador",
        # outros serviços gerais
        "professor particular", "consultor", "consultoria",
        "assistência técnica", "instalação", "instalador",
    ],
    AtividadeMEI.COMERCIO_INDUSTRIA: [
        "loja", "loja de roupa", "mercearia", "mercado",
        "lanchonete", "restaurante", "sorveteria", "padaria",
        "ecommerce", "e-commerce", "brecho", "brechó",
        "bazar", "armazém", "venda de produtos", "comércio",
        "fabricação", "fábrica", "produção",
    ],
    AtividadeMEI.COMERCIO_SERVICOS: [
        "mecânico", "mecanico", "oficina", "auto center",
        "assistência técnica", "assistencia tecnica",
        "conserto", "manutenção com peças",
        "loja de celular com conserto",
        "vende e instala", "vende e presta serviço",
    ],
    AtividadeMEI.CAMINHONEIRO: [
        "caminhoneiro", "transporte de cargas", "frete pesado",
        "tac", "carga interestadual", "carga intermunicipal",
    ],
}


@dataclass
class ResultadoMEI:
    # Situação atual
    faturamento_anual: float
    meses_atividade: int
    limite_proporcional: float
    percentual_uso: float
    faixa_situacao: str
    mensagem_situacao: str
    valor_das: float
    atividade_label: str

    # Projeção até dezembro, mantendo o mesmo ritmo
    faturamento_mensal_medio: float
    faturamento_projetado_ano: float
    percentual_uso_projetado: float
    faixa_situacao_projetada: str
    mensagem_projetada: str

    # INSS
    inss_mensal: float
    inss_anual: float
    inss_complementar_mensal: float
    inss_total_mensal_complementado: float


def _obter_valor_das(atividade: AtividadeMEI, config: Config) -> float:
    """
    Retorna o valor aproximado do DAS conforme a atividade.

    Aqui usamos os valores pré-configurados em Config.
    Em produção real, esses valores podem ser atualizados anualmente.
    """
    if atividade == AtividadeMEI.COMERCIO_INDUSTRIA:
        return config.DAS_COMERCIO_INDUSTRIA
    if atividade == AtividadeMEI.SERVICOS:
        return config.DAS_SERVICOS
    if atividade == AtividadeMEI.COMERCIO_SERVICOS:
        return config.DAS_COMERCIO_SERVICOS
    return config.DAS_CAMINHONEIRO_MIN


def _classificar_situacao(
    faturamento: float,
    limite_base: float,
    tolerancia: float,
) -> tuple[str, str, float]:
    """
    Classifica em confortável / atenção / tolerância / estourado.

    Retorna:
      - faixa_situacao: string curta para usar em lógica/estilo
      - mensagem: explicação amigável
      - percentual: quanto do limite foi utilizado (0.0 a 1.x)
    """

    if limite_base <= 0:
        return "desconhecido", "Não foi possível calcular.", 0.0

    percentual = faturamento / limite_base
    limite_tolerado = limite_base * (1 + tolerancia)

    if percentual <= 0.8:
        faixa = "confortavel"
        msg = "Você está bem dentro do limite de faturamento do MEI."
    elif percentual <= 1.0:
        faixa = "atencao"
        msg = "Atenção: você está se aproximando do limite de faturamento do MEI."
    elif faturamento <= limite_tolerado:
        faixa = "tolerancia"
        msg = (
            "Você ultrapassou o limite do MEI, mas ainda está dentro da "
            "margem de tolerância de 20%. É importante conversar com uma "
            "contabilidade sobre possíveis impactos."
        )
    else:
        faixa = "estourado"
        msg = (
            "Seu faturamento está acima do limite do MEI e da margem de "
            "tolerância. Muito provavelmente será necessário migrar para "
            "outro regime (ME ou EPP)."
        )

    return faixa, msg, percentual


# 🔹 NOVO: função de apoio para UX
def sugerir_atividade_por_descricao(descricao: str) -> Optional[AtividadeMEI]:
    """
    Tenta sugerir o grupo de atividade (comércio/serviços/etc.)
    com base em um texto livre digitado pelo usuário.

    Exemplo de entradas:
      - "Sou motorista de Uber"
      - "Faço entrega no iFood de moto"
      - "Tenho uma loja de roupas"
      - "Sou desenvolvedor e faço sites"

    Retorna:
      - AtividadeMEI correspondente, se encontrar alguma palavra-chave
      - None, se não conseguir sugerir nada com segurança
    """
    if not descricao:
        return None

    desc = descricao.lower()
    melhor_atividade: Optional[AtividadeMEI] = None
    melhor_score = 0

    # Conta quantas "keywords" de cada grupo aparecem no texto
    for atividade, keywords in ATIVIDADE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in desc:
                score += 1

        # Guarda o grupo com maior número de matches
        if score > melhor_score:
            melhor_score = score
            melhor_atividade = atividade

    # Se não achou nenhuma palavra, não devemos sugerir nada
    if melhor_score == 0:
        return None

    return melhor_atividade


# 🔹 NOVO: texto explicativo por grupo (para usar no front, se quiser)
def obter_texto_explicacao_atividade(atividade: AtividadeMEI) -> str:
    """
    Retorna um texto explicando, em linguagem simples, para quem
    aquele grupo de atividade é indicado.

    Útil para exibir abaixo do campo de seleção ou em tooltips.
    """
    if atividade == AtividadeMEI.SERVICOS:
        return (
            "Use 'Serviços' se você trabalha prestando serviços em geral: "
            "Uber, 99, iFood de moto, entregas, pedreiro, pintor, eletricista, "
            "programador, designer, manicure, barbeiro, fotógrafo, professor "
            "particular, consultor e similares."
        )
    if atividade == AtividadeMEI.COMERCIO_INDUSTRIA:
        return (
            "Use 'Comércio / Indústria' se você vende produtos ou fabrica algo: "
            "loja de roupas, mercearia, mercado, lanchonete, restaurante, "
            "artesanato, padaria, e-commerce e outras vendas de produtos."
        )
    if atividade == AtividadeMEI.COMERCIO_SERVICOS:
        return (
            "Use 'Comércio + Serviços' se você vende produtos e também presta "
            "serviços relacionados: mecânico que vende peças e mão de obra, "
            "assistência técnica que vende e instala, loja de celular com conserto, etc."
        )
    if atividade == AtividadeMEI.CAMINHONEIRO:
        return (
            "Use 'MEI Caminhoneiro' se você atua principalmente com transporte "
            "de cargas como transportador autônomo (TAC), fazendo fretes e "
            "viagens intermunicipais ou interestaduais."
        )
    return (
        "Escolha o grupo que mais se aproxima da sua atividade principal: "
        "Serviços, Comércio, Comércio + Serviços ou Caminhoneiro."
    )


def calcular_situacao_mei(
    faturamento_anual: float,
    meses_atividade: int,
    atividade: AtividadeMEI,
    config: Config | None = None,
) -> ResultadoMEI:
    """
    Calcula a situação atual, projeção e INSS do MEI.

    Esse é o "core" da regra de negócio:
      - aplica limite proporcional ao tempo de atividade
      - classifica a situação do faturamento
      - projeta o ano mantendo o mesmo ritmo
      - calcula INSS (5%) e complemento opcional (15%)
    """

    config = config or Config()
    meses_atividade = max(1, min(meses_atividade, 12))

    # Situação atual (limite proporcional ao tempo de atividade)
    limite_proporcional = config.MEI_LIMITE_ANUAL * (meses_atividade / 12)
    faixa_atual, msg_atual, percentual_uso = _classificar_situacao(
        faturamento=faturamento_anual,
        limite_base=limite_proporcional,
        tolerancia=config.MEI_TOLERANCIA_EXCESSO,
    )

    # Projeção: se mantiver o mesmo ritmo até completar 12 meses
    faturamento_mensal_medio = (
        faturamento_anual / meses_atividade if meses_atividade > 0 else 0.0
    )
    faturamento_projetado_ano = faturamento_mensal_medio * 12

    faixa_proj, msg_proj, perc_proj = _classificar_situacao(
        faturamento=faturamento_projetado_ano,
        limite_base=config.MEI_LIMITE_ANUAL,
        tolerancia=config.MEI_TOLERANCIA_EXCESSO,
    )

    valor_das = _obter_valor_das(atividade, config)
    atividade_label = ATIVIDADE_LABELS[atividade]

    # INSS: 5% do salário mínimo (MEI) + complemento opcional de 15%
    inss_mensal = round(config.SALARIO_MINIMO * config.INSS_ALIQUOTA_MEI, 2)
    inss_anual = round(inss_mensal * 12, 2)
    inss_complementar_mensal = round(
        config.SALARIO_MINIMO * config.INSS_ALIQUOTA_COMPLEMENTAR, 2
    )
    inss_total_mensal_complementado = round(
        inss_mensal + inss_complementar_mensal, 2
    )

    return ResultadoMEI(
        faturamento_anual=round(faturamento_anual, 2),
        meses_atividade=meses_atividade,
        limite_proporcional=round(limite_proporcional, 2),
        percentual_uso=percentual_uso,
        faixa_situacao=faixa_atual,
        mensagem_situacao=msg_atual,
        valor_das=round(valor_das, 2),
        atividade_label=atividade_label,
        faturamento_mensal_medio=round(faturamento_mensal_medio, 2),
        faturamento_projetado_ano=round(faturamento_projetado_ano, 2),
        percentual_uso_projetado=perc_proj,
        faixa_situacao_projetada=faixa_proj,
        mensagem_projetada=msg_proj,
        inss_mensal=inss_mensal,
        inss_anual=inss_anual,
        inss_complementar_mensal=inss_complementar_mensal,
        inss_total_mensal_complementado=inss_total_mensal_complementado,
    )
