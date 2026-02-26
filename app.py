from flask import Flask
from config import Config
from extensions import db, login_manager, mail, migrate


def create_app():
    import os

    app = Flask(__name__)

    # 🔐 Load Config class (important)
    app.config.from_object(Config)

    # 🔐 Ensure SECRET_KEY exists (fallback for safety)
    app.config["SECRET_KEY"] = app.config.get(
        "SECRET_KEY", "dev_secret_key_123"
    )

    # 🗄 Database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skillswap.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 📂 Upload folder
    app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.dashboard import dashboard_bp
    from routes.courses import courses_bp
    from routes.payment import payment_bp
    from routes.live import live_bp
    from routes.certificate import certificate_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(certificate_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)