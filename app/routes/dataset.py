import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app.services.etl_service import clean_and_process_dataset
from app.models import Dataset
from app import db

data_bp = Blueprint('dataset', __name__, url_prefix='/dataset')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

@data_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                raw_name = file.filename.rsplit('.', 1)[0]
                # user_id=1 as shared open platform
                dataset = clean_and_process_dataset(filepath, filename, 1, raw_name)
                flash('Dataset uploaded and processed successfully!', 'success')
                return redirect(url_for('dash.analytica', dataset_id=dataset.id))
            except Exception as e:
                flash(f'Error processing dataset: {str(e)}', 'error')
                return redirect(request.url)
                
    return render_template('upload.html')

@data_bp.route('/delete/<int:dataset_id>', methods=['POST'])
def delete(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    engine = db.engine
    with engine.connect() as con:
        con.execute(f"DROP TABLE IF EXISTS {dataset.table_name}")
    db.session.delete(dataset)
    db.session.commit()
    flash('Dataset deleted', 'success')
    return redirect(url_for('dash.home'))
