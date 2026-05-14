from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Transaction, Budget
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    transactions = (
        Transaction.query.filter_by(user_id=current_user.id)
        .order_by(Transaction.date_created.desc())
        .all()
    )

    total_income = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_expense = sum(
        t.amount for t in transactions if t.transaction_type == "expense"
    )
    balance = total_income - total_expense

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
    )


@app.route("/add_transaction", methods=["GET", "POST"])
@login_required
def add_transaction():
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        description = request.form.get("description")

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than zero.", "danger")
                return redirect(url_for("add_transaction"))
        except ValueError:
            flash("Please enter a valid amount.", "danger")
            return redirect(url_for("add_transaction"))

        new_transaction = Transaction(
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            description=description,
            user_id=current_user.id,
        )

        db.session.add(new_transaction)
        db.session.commit()

        flash("Transaction added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_transaction.html")


# Route for editing an existing transaction
# This route allows users to edit an existing transaction
# The transaction ID is passed through the URL
@app.route("/edit_transaction/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    # Find the transaction by ID and make sure it belongs to the logged-in user
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=current_user.id
    ).first_or_404()

    # If the form is submitted, update the transaction
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type")
        category = request.form.get("category")
        amount = request.form.get("amount")
        description = request.form.get("description")

        # Validate amount
        try:
            amount = float(amount)

            # Prevent zero or negative values
            if amount <= 0:
                flash("Amount must be greater than zero.", "danger")

                # Redirect back to edit page if validation fails
                return redirect(
                    url_for("edit_transaction", transaction_id=transaction.id)
                )
        except ValueError:
            flash("Please enter a valid amount.", "danger")
            return redirect(url_for("edit_transaction", transaction_id=transaction.id))

        # Update transaction details
        transaction.transaction_type = transaction_type
        transaction.category = category
        transaction.amount = amount
        transaction.description = description

        # Save changes to database
        db.session.commit()

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("dashboard"))

    # Show edit form with existing transaction details
    return render_template("edit_transaction.html", transaction=transaction)


# Route for deleting a transaction
@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    # Find the transaction and check ownership
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=current_user.id
    ).first_or_404()

    # Delete transaction from database
    db.session.delete(transaction)
    db.session.commit()

    flash("Transaction deleted successfully.", "info")
    return redirect(url_for("dashboard"))


# Route for budget management
@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():

    # Add new budget
    if request.method == "POST":

        category = request.form.get("category")
        monthly_limit = request.form.get("monthly_limit")

        try:
            monthly_limit = float(monthly_limit)

            if monthly_limit <= 0:
                flash("Budget amount must be greater than zero.", "danger")
                return redirect(url_for("budgets"))

        except ValueError:
            flash("Please enter a valid budget amount.", "danger")
            return redirect(url_for("budgets"))

        # Create new budget
        new_budget = Budget(
            category=category, monthly_limit=monthly_limit, user_id=current_user.id
        )

        db.session.add(new_budget)
        db.session.commit()

        flash("Budget added successfully.", "success")
        return redirect(url_for("budgets"))

    # Get all budgets for logged-in user
    user_budgets = Budget.query.filter_by(user_id=current_user.id).all()

    return render_template("budgets.html", budgets=user_budgets)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
