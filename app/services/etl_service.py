import pandas as pd
import numpy as np
import uuid
import json
from app import db
from app.models import Dataset
from sqlalchemy import create_engine
from flask import current_app

def clean_and_process_dataset(file_path, original_filename, user_id, dataset_name):
    # 1. Read file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

    if df.empty:
        df = pd.DataFrame({"Data": [0]})

    # Strip column names of trailing spaces
    df.columns = df.columns.str.strip()

    # 2. Heuristics for Column Detection
    # Standardize column names (strip spaces, lower case for internal heuristics, but keep original for display if we want. Actually, let's keep original for UI but use lower for comparison)
    date_col = None
    metric_cols = []
    category_cols = []

    # Attempt to find the best Date column (Prioritize Date/Day over Year/Month)
    potential_date_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ['date', 'time', 'day', 'month', 'year', 'timestamp']):
            try:
                # Test if it can be converted to datetime
                parsed = pd.to_datetime(df[col], errors='coerce')
                if parsed.notna().sum() > len(df) * 0.3: # At least 30% valid dates
                    # Rank them: Date/Day/Time/Timestamp get +2 points
                    score = 0
                    if any(x in col_lower for x in ['date', 'day', 'time', 'timestamp']): score += 2
                    # Variance check: columns with more unique values are better candidates for trend lines
                    variance = df[col].nunique()
                    potential_date_cols.append({"col": col, "score": score, "variance": variance})
            except:
                pass
                
    if potential_date_cols:
        # Sort by Score (Keywords) first, then by Variance (Unique Values)
        potential_date_cols.sort(key=lambda x: (x['score'], x['variance']), reverse=True)
        date_col = potential_date_cols[0]['col']
                
    if not date_col:
        # Fallback: try all columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    if parsed.notna().sum() > len(df) * 0.5: # 50% are dates
                        date_col = col
                        break
                except:
                    pass

    # Find Metrics (Sales, Revenue, Quantity, Price, etc)
    for col in df.columns:
        if col == date_col: continue
        if pd.api.types.is_numeric_dtype(df[col]):
            metric_cols.append(col)
        else:
            # Check if it's a string that should be numeric (e.g. "$1,000")
            try:
                # Remove common currency symbols and commas
                cleaned = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                test_num = pd.to_numeric(cleaned, errors='coerce')
                if test_num.notna().sum() > len(df) * 0.5:
                    df[col] = test_num
                    metric_cols.append(col)
                else:
                    category_cols.append(col)
            except:
                category_cols.append(col)

    if not metric_cols:
        # Fallback: Create a static metric column if dataset is entirely text/dates
        df['_Metric_Count'] = 1
        metric_cols.append('_Metric_Count')

    # Prioritize Sales / Revenue as primary metric
    primary_metric = metric_cols[0]
    for col in metric_cols:
        if any(x in col.lower() for x in ['sale', 'rev', 'total', 'amount', 'profit', 'qty']):
            primary_metric = col
            break

    # 3. Clean the Data
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        if len(df) == 0:
            df = pd.DataFrame({"Data": [0]}) # Fallback if everything dropped
        else:
            df = df.sort_values(by=date_col)

    # For metrics, fill missing with 0 (or median, but 0 is safer for sales)
    for col in metric_cols:
        df[col] = df[col].fillna(0)

    # For categories, fill missing with 'Unknown'
    for col in category_cols:
        df[col] = df[col].fillna('Unknown').astype(str)

    # 4. Save to Database (Dynamic Table)
    table_name = f"dataset_{uuid.uuid4().hex}"
    
    # We use Pandas to_sql directly to the SQLite database
    engine = db.engine
    # To handle large datasets, chunksize helps
    df.to_sql(table_name, con=engine, index=False, if_exists='replace', chunksize=1000)

    # 5. Metadata for DB
    metadata = {
        "date_col": date_col,
        "primary_metric": primary_metric,
        "all_metrics": metric_cols,
        "categories": category_cols
    }

    dataset = Dataset(
        name=dataset_name,
        filename=original_filename,
        table_name=table_name,
        user_id=user_id,
        metadata_json=json.dumps(metadata),
        row_count=len(df)
    )
    db.session.add(dataset)
    db.session.commit()

    return dataset
