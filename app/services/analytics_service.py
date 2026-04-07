import pandas as pd
from app import db
import json

def get_dashboard_data(dataset, filters=None):
    """
    Returns KPIs and chart groupings.
    Filters: list of dicts [{'col': 'Category', 'val': 'Electronics'}, ...]
    """
    engine = db.engine
    
    # Base query
    query = f"SELECT * FROM {dataset.table_name}"
    
    # If filters provided, query with where clauses (Note: parameterized queries are safest, doing it via pandas)
    df = pd.read_sql(query, engine)
    
    metadata = json.loads(dataset.metadata_json)
    date_col = metadata.get('date_col')
    primary_metric = metadata.get('primary_metric')
    category_cols = metadata.get('categories', [])
    
    # Live Fallback: If date_col is missing from metadata, try to find one in the DF
    if not date_col:
        for col in df.columns:
            if any(x in col.lower() for x in ['date', 'time', 'day', 'timestamp']):
                parsed = pd.to_datetime(df[col], errors='coerce')
                if parsed.notna().sum() > 0:
                    date_col = col
                    break
    
    # Apply filters
    if filters:
        for f in filters:
            col = f.get('col')
            val = f.get('val')
            if col in df.columns:
                df = df[df[col].astype(str) == str(val)]
                
    if df.empty:
        return {"error": "No data available with the current filters."}

    # KPIs
    total_sales = df[primary_metric].sum() if primary_metric else 0
    kpis = {
        "Total Sales": float(total_sales),
        "Rows Count": len(df)
    }

    charts_data = {}

    # Category Charts (Top 5 for max 2 categories)
    for cat in category_cols[:2]:
        grouped_cat = df.groupby(cat)[primary_metric].sum().nlargest(5).to_dict()
        charts_data[f"Top 5 {cat}"] = grouped_cat

    # Trend Chart (Group by Date)
    trend_data = {}
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        if not df.empty:
            date_range = (df[date_col].max() - df[date_col].min()).days
            # Adaptive Resampling: Daily for short periods, Weekly for long
            resample_freq = '1D' if date_range < 60 else '1W'
            trend_df = df.groupby(pd.Grouper(key=date_col, freq=resample_freq)).sum(numeric_only=True)
            trend_data = {str(k.date()): float(v) for k, v in trend_df[primary_metric].items()}
            charts_data["Weekly Trend"] = trend_data

    # Find the top product generically
    # assume the column with max unique values > 10 but < 5000 is product name
    top_product = "N/A"
    for cat in category_cols:
        nunique = df[cat].nunique()
        if 5 < nunique < 5000:
            top_cat = df.groupby(cat)[primary_metric].sum().nlargest(1)
            if not top_cat.empty:
                top_product = f"{top_cat.index[0]} ({top_cat.values[0]:.2f})"
            break
            
    kpis["Top Performer"] = top_product

    # Extract all unique values for categories to populate the filter dropdowns in UI
    filter_options = {}
    for cat in category_cols:
        # only provide filters if unique values are manageable
        if df[cat].nunique() < 50:
            filter_options[cat] = df[cat].unique().tolist()

    return {
        "kpis": kpis,
        "charts": charts_data,
        "filters": filter_options,
        "metadata": metadata
    }
