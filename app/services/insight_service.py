import pandas as pd
from app import db
import json

def generate_insights(dataset):
    engine = db.engine
    query = f"SELECT * FROM {dataset.table_name}"
    df = pd.read_sql(query, engine)
    
    metadata = json.loads(dataset.metadata_json)
    date_col = metadata.get('date_col')
    primary_metric = metadata.get('primary_metric')
    category_cols = metadata.get('categories', [])
    
    insights = []
    
    if df.empty:
        return ["No data available to generate insights."]

    # 1. Overall Growth
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        recent = df.dropna(subset=[date_col]).sort_values(by=date_col)
        # Compare last 30 days vs previous 30 days
        max_date = recent[date_col].max()
        last_30 = recent[recent[date_col] >= max_date - pd.Timedelta(days=30)][primary_metric].sum()
        prev_30 = recent[(recent[date_col] >= max_date - pd.Timedelta(days=60)) & (recent[date_col] < max_date - pd.Timedelta(days=30))][primary_metric].sum()
        
        if prev_30 > 0:
            growth = ((last_30 - prev_30) / prev_30) * 100
            trend = "up" if growth > 0 else "down"
            insights.append({
                "type": "success" if growth > 0 else "warning",
                "title": f"Recent 30-Day Growth",
                "message": f"Your {primary_metric} are {trend} by {abs(growth):.1f}% compared to the previous 30 days."
            })

    # 2. Category Concentration
    for cat in category_cols[:2]:
        if df[cat].nunique() < 20: # Ensure it's a manageable category
            grouped = df.groupby(cat)[primary_metric].sum()
            total = grouped.sum()
            top_cat = grouped.nlargest(1)
            if not top_cat.empty and total > 0:
                pct = (top_cat.values[0] / total) * 100
                insights.append({
                    "type": "info",
                    "title": f"Top {cat.capitalize()} Dependency",
                    "message": f"'{top_cat.index[0]}' accounts for {pct:.1f}% of total {primary_metric}. Consider diversifying your focus."
                })

    # 3. Anomaly Detection (Very basic: day with 3x average)
    if date_col:
        daily = df.groupby(pd.Grouper(key=date_col, freq='1D'))[primary_metric].sum()
        avg_daily = daily.mean()
        std_daily = daily.std()
        anomalies = daily[daily > avg_daily + 2 * std_daily]
        if not anomalies.empty:
            peak = anomalies.idxmax()
            insights.append({
                "type": "warning",
                "title": "Unusual Spike Detected",
                "message": f"We detected an unusual spike in {primary_metric} on {peak.date()} ({anomalies.max():.2f}). Investigate what caused this positive anomaly to replicate it."
            })
            
    if not insights:
        insights.append({
            "type": "info",
            "title": "Stable Baseline",
            "message": "Data is tracking along expected baselines with no major anomalies detected."
        })

    return insights
