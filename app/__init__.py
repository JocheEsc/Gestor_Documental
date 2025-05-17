# app/__init__.py

from flask import Flask
from .routes import routes_blueprint  # ✅ Importación correcta del Blueprint

def create_app():
    app = Flask(__name__)
    app.secret_key = 'tu_clave_secreta'

    app.register_blueprint(routes_blueprint)

    return app