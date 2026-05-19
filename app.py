import os
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///finance.db"
)
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


# Route for forgotten password reset
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        new_password = request.form.get("new_password")

        # Find user by username and email
        user = User.query.filter(
            User.username.ilike(username), User.email.ilike(email)
        ).first()

        if not user:
            flash("No account found with those details.", "danger")
            return redirect(url_for("forgot_password"))

        # Hash and update new password
        user.password_hash = generate_password_hash(new_password)

        db.session.commit()

        flash("Password reset successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


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

    # Prepare expense category data for chart
    expense_by_category = {}

    for transaction in transactions:
        if transaction.transaction_type == "expense":
            category = transaction.category
            expense_by_category[category] = (
                expense_by_category.get(category, 0) + transaction.amount
            )

    chart_labels = list(expense_by_category.keys())
    chart_values = list(expense_by_category.values())

    # Get selected month from dashboard filter
    selected_month = request.args.get("month")

    # If no month is selected, use current transaction month if available
    if not selected_month and transactions:
        selected_month = transactions[0].date_created.strftime("%Y-%m")

    # Prepare category expenses for selected month
    monthly_category_expenses = {}

    for transaction in transactions:
        if transaction.transaction_type == "expense":
            transaction_month = transaction.date_created.strftime("%Y-%m")

            if transaction_month == selected_month:
                category = transaction.category
                monthly_category_expenses[category] = (
                    monthly_category_expenses.get(category, 0) + transaction.amount
                )

    monthly_labels = list(monthly_category_expenses.keys())
    monthly_values = list(monthly_category_expenses.values())

    return render_template(
        "dashboard.html",
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        chart_labels=chart_labels,
        chart_values=chart_values,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        selected_month=selected_month,
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

    # Store budget warning information
    budget_data = []

    # Compare budgets with expenses
    for budget in user_budgets:

        # Calculate total expense for matching category
        total_spent = sum(
            transaction.amount
            for transaction in Transaction.query.filter_by(
                user_id=current_user.id,
                category=budget.category,
                transaction_type="expense",
            ).all()
        )

        # Remaining budget
        remaining = budget.monthly_limit - total_spent

        # Check if exceeded
        exceeded = total_spent > budget.monthly_limit

        # Save values for HTML page
        budget_data.append(
            {
                "id": budget.id,
                "category": budget.category,
                "monthly_limit": budget.monthly_limit,
                "spent": total_spent,
                "remaining": remaining,
                "exceeded": exceeded,
            }
        )

    return render_template("budgets.html", budgets=budget_data)


# Update budget from the same budget page
@app.route("/update_budget/<int:budget_id>", methods=["POST"])
@login_required
def update_budget(budget_id):
    budget = Budget.query.filter_by(
        id=budget_id, user_id=current_user.id
    ).first_or_404()

    budget.category = request.form.get("category")
    budget.monthly_limit = float(request.form.get("monthly_limit"))

    db.session.commit()
    flash("Budget updated successfully.", "success")

    return redirect(url_for("budgets"))


# Delete budget from the same budget page
@app.route("/delete_budget/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(
        id=budget_id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(budget)
    db.session.commit()
    flash("Budget deleted successfully.", "info")

    return redirect(url_for("budgets"))


with app.app_context():
    db.create_all()


# Admin route to view users
@app.route("/all_users")
def all_users():

    users = User.query.all()

    return render_template("all_users.html", users=users)


if __name__ == "__main__":
    app.run(debug=True)
