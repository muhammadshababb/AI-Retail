import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 's3cr3t_a1_k3y_r3ta1l'
    
    # SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'retail_ai.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Uploads folder
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)
    
    with app.app_context():
        from app import models
        db.create_all()

    # Blueprints
    from app.routes.dashboard import dash_bp
    from app.routes.dataset import data_bp
    
    app.register_blueprint(dash_bp)
    app.register_blueprint(data_bp)

    return app
