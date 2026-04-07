from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    datasets = db.relationship('Dataset', backref='user', lazy=True)

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(250), nullable=False)
    table_name = db.Column(db.String(100), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stores JSON metadata about the detected columns
    # Example: {"date_col": "OrderDate", "metric_col": "Sales", "category_cols": ["District", "Category"]}
    metadata_json = db.Column(db.Text, nullable=True)
    
    row_count = db.Column(db.Integer, default=0)
