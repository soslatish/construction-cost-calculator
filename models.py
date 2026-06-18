from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

ROLE_VIEWER = 'viewer'
ROLE_MANAGER = 'manager'
ROLE_ADMIN = 'admin'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_VIEWER)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    calculations = db.relationship('Calculation', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_manager(self):
        return self.role == ROLE_MANAGER

    @property
    def can_edit(self):
        return self.role in (ROLE_ADMIN, ROLE_MANAGER)


class Calculation(db.Model):
    __tablename__ = 'calculations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    total_area = db.Column(db.Float, nullable=False)
    floors = db.Column(db.Integer, nullable=False)
    foundation_type = db.Column(db.String(50), nullable=False)
    roof_type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, default='')
    total_cost = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('CalculationItem', backref='calculation', lazy=True, cascade='all, delete-orphan')


class CalculationItem(db.Model):
    __tablename__ = 'calculation_items'

    id = db.Column(db.Integer, primary_key=True)
    calculation_id = db.Column(db.Integer, db.ForeignKey('calculations.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(20), default='')
    quantity = db.Column(db.Float, default=0.0)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
