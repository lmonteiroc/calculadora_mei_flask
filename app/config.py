class Config:
    """Configuração base e constantes do MEI 2025."""

    SECRET_KEY = "dev-change-me"
    APP_NAME = "Calculadora MEI 2025"

    # Limite anual MEI (ajuste se o governo mudar o valor)
    MEI_LIMITE_ANUAL = 81_000.00
    MEI_TOLERANCIA_EXCESSO = 0.20  # até 20% acima do limite

    # Valores aproximados do DAS-MEI (exemplo)
    DAS_COMERCIO_INDUSTRIA = 76.90
    DAS_SERVICOS = 80.90
    DAS_COMERCIO_SERVICOS = 81.90
    DAS_CAMINHONEIRO_MIN = 183.16

    # INSS / previdência
    # Salário mínimo de referência (ajustar por ano)
    SALARIO_MINIMO = 1412.00

    # Alíquota de contribuição do MEI (INSS) sobre o salário mínimo
    INSS_ALIQUOTA_MEI = 0.05  # 5%

    # Complemento opcional para chegar em 20% (código 1910)
    INSS_ALIQUOTA_COMPLEMENTAR = 0.15  # 15% adicionais

    # Carência mínima para aposentadoria por idade (em meses)
    CARENCIA_APOSENTADORIA_IDADE = 180
