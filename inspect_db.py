from app import create_app, db
from app.models import Dataset
import json

app = create_app()
with app.app_context():
    datasets = Dataset.query.all()
    for d in datasets:
        print(f"ID: {d.id} | Name: {d.name} | Table: {d.table_name}")
        print(f"  Rows: {d.row_count} | Uploaded: {d.uploaded_at}")
        try:
            meta = json.loads(d.metadata_json) if d.metadata_json else {}
            print(f"  Meta: {meta}")
        except:
            print(f"  Meta: ERROR PARSING")
        print("-" * 30)
