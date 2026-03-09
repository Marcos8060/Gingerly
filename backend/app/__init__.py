from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}})

    from app.auth.routes import auth_bp
    from app.contacts.routes import contacts_bp
    from app.emails.routes import emails_bp
    from app.groups.routes import groups_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contacts_bp, url_prefix="/api/contacts")
    app.register_blueprint(emails_bp, url_prefix="/api/emails")
    app.register_blueprint(groups_bp, url_prefix="/api/groups")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    swaggerui_bp = get_swaggerui_blueprint(
        "/api/docs",
        "/api/docs/openapi.yaml",
        config={"app_name": "Gingerly API"},
    )
    app.register_blueprint(swaggerui_bp, url_prefix="/api/docs")

    @app.route("/api/docs/openapi.yaml")
    def openapi_spec():
        return send_from_directory("../static", "openapi.yaml")

    @app.route("/api")
    def health():
        return jsonify({"status": "ok", "message": "Gingerly API is running"}), 200

    with app.app_context():
        db.create_all()

    return app
