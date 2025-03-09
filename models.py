from app import db
from datetime import datetime

class ProductionCell(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    components = db.relationship('Component', backref='cell', lazy=True)

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cell_id = db.Column(db.Integer, db.ForeignKey('production_cell.id'), nullable=False)
    completion_time = db.Column(db.Float, nullable=False)  # Time in minutes
    min_operators = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
