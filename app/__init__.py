from flask import Flask

from .config import Config
from .routes import main_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Blueprints
    app.register_blueprint(main_bp)

    # Variáveis globais para todos os templates
    @app.context_processor
    def inject_globals():
        return {"APP_NAME": app.config.get("APP_NAME", "Calculadora MEI 2025")}

    return app

