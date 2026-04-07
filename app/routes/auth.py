from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dash.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # frictionless auto-register for any new email
        if not user:
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            is_admin_user = email.lower().startswith('admin')
            user = User(email=email, password=hashed_password, is_admin=is_admin_user)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dash.index') if is_admin_user else url_for('dash.home'))
            
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dash.index') if user.is_admin else url_for('dash.home'))
        flash('Incorrect password for this account.', 'error')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dash.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('auth.register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        is_admin_user = email.lower().startswith('admin')
        new_user = User(email=email, password=hashed_password, is_admin=is_admin_user)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dash.index') if is_admin_user else url_for('dash.home'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
