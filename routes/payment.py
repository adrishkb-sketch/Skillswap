from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import CreditTransaction

payment_bp = Blueprint('payment', __name__)


@payment_bp.route("/buy-credits", methods=["GET", "POST"])
@login_required
def buy_credits():

    if request.method == "POST":

        amount = int(request.form.get("amount"))

        # Fake success payment
        current_user.credits += amount
        current_user.bought_credits += amount

        db.session.add(CreditTransaction(
            user_id=current_user.id,
            amount=amount,
            type="purchase"
        ))

        db.session.commit()

        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("buy_credits.html")