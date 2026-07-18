from flask import Flask
from app.config import get_config


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    
    app_config = get_config()
    app.config["APP_CONFIG"] = app_config

    from app.routes import bp as kiosk_bp

    app.register_blueprint(kiosk_bp)

    return app