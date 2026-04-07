from flask import Blueprint, render_template, request, jsonify, url_for, redirect
from app.models import Dataset
from app.services.analytics_service import get_dashboard_data
from app.services.ml_service import generate_forecast
from app.services.insight_service import generate_insights

dash_bp = Blueprint('dash', __name__)

@dash_bp.route('/')
def index():
    return redirect(url_for('dash.home'))

@dash_bp.route('/home')
def home():
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    total_rows = sum(d.row_count for d in datasets) if datasets else 0
    return render_template('about.html', datasets=datasets, total_rows=total_rows)

@dash_bp.route('/api/stats')
def stats():
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    latest = datasets[0] if datasets else None
    return jsonify({
        "total_datasets": len(datasets),
        "total_rows": sum(d.row_count for d in datasets) if datasets else 0,
        "latest_dataset_id": latest.id if latest else None,
        "datasets": [{"id": d.id, "name": d.name} for d in datasets]
    })

@dash_bp.route('/schema')
def schema():
    return render_template('schema.html')

@dash_bp.route('/settings')
def settings():
    return render_template('settings.html')

@dash_bp.route('/analytics/<int:dataset_id>')
def analytica(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    return render_template('dashboard.html', datasets=datasets, current_dataset=dataset)

@dash_bp.route('/api/data/<int:dataset_id>', methods=['POST'])
def get_data(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    filters = request.json.get('filters', [])
    data = get_dashboard_data(dataset, filters)
    return jsonify(data)

@dash_bp.route('/api/forecast/<int:dataset_id>', methods=['POST'])
def get_forecast(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    filters = request.json.get('filters', [])
    days = request.json.get('days', 30)
    data = generate_forecast(dataset, days, filters)
    return jsonify(data)

@dash_bp.route('/api/insights/<int:dataset_id>', methods=['GET'])
def get_insights(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    insights = generate_insights(dataset)
    return jsonify({"insights": insights})
