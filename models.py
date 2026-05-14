from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    transactions = db.relationship("Transaction", backref="user", lazy=True)


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # income or expense
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


# Budget table model
class Budget(db.Model):
    __tablename__ = "budgets"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Budget category (Food, Travel, etc.)
    category = db.Column(db.String(100), nullable=False)

    # Monthly budget limit
    monthly_limit = db.Column(db.Float, nullable=False)

    # Relationship to user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
