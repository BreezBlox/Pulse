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

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs = db.relationship('Job', backref='customer', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_completion_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Queued')  # Queued, In Progress, Completed
    total_hours = db.Column(db.Float)  # Calculated from components
    min_operators = db.Column(db.Integer)  # Calculated from components
    max_operators = db.Column(db.Integer)  # Calculated from components
    current_operators = db.Column(db.Integer, default=0)
    components = db.relationship('JobComponent', backref='job', lazy=True)

class JobComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('component.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    actual_completion_time = db.Column(db.Float)  # Actual time taken to complete
    operators = db.Column(db.Integer)  # Number of operators who worked on this
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)