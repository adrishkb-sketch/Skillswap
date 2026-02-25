from flask import Flask
from config import Config
from extensions import db, login_manager, mail, migrate
import cloudinary

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    # Configure Cloudinary
    cloudinary.config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"],
        secure=True
    )

    # IMPORTANT FOR INDIA / AP REGION
    cloudinary.config(api_base_url="https://api-ap.cloudinary.com")
    print("Cloud Name:", app.config["CLOUDINARY_CLOUD_NAME"])
    print("API Key:", app.config["CLOUDINARY_API_KEY"])
    print("API Secret:", app.config["CLOUDINARY_API_SECRET"])
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