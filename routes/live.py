from flask import Blueprint

live_bp = Blueprint('live', __name__)

@live_bp.route("/live-test")
def test_live():
    return "Live Blueprint Working"