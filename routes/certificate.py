from flask import Blueprint

certificate_bp = Blueprint('certificate', __name__)

@certificate_bp.route("/certificate-test")
def test_certificate():
    return "Certificate Blueprint Working"