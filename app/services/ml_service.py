import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error
from app import db
import json

def generate_forecast(dataset, days=30, filters=None):
    engine = db.engine
    query = f"SELECT * FROM {dataset.table_name}"
    df = pd.read_sql(query, engine)
    
    metadata = json.loads(dataset.metadata_json)
    date_col = metadata.get('date_col')
    primary_metric = metadata.get('primary_metric')
    
    if not date_col or not primary_metric:
        return {"error": "Missing Date or Metric column for forecasting."}
    if df.empty:
        df = pd.DataFrame({"Data": [0]})

    # Strip column names of trailing spaces
    df.columns = df.columns.str.strip()

    # 2. Heuristics for Column Detection
    if filters:
        for f in filters:
            col = f.get('col')
            val = f.get('val')
            if col in df.columns:
                df = df[df[col].astype(str) == str(val)]

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Re-calculate daily_df after filtering
    daily_df = df.groupby(pd.Grouper(key=date_col, freq='1D'))[primary_metric].sum().reset_index()
    daily_df = daily_df.set_index(date_col)
    
    # Needs at least some data points for Trend; 14+ for high-quality forecast
    if len(daily_df) < 2:
        return {"error": "Insufficient data (at least 2 days needed).", "historical": {}, "forecast": {}}
        
    # If not enough for a real forecast, return historical only
    if len(daily_df) < 14:
        return {
            "historical": {str(k.date()): float(v) for k, v in daily_df[primary_metric].items()},
            "forecast": {},
            "warning": "Need at least 14 days of data for reliable AI forecasting."
        }
        
    # Forward fill 0 for missing days
    # To keep model from breaking on missing days within range
    idx = pd.date_range(daily_df.index.min(), daily_df.index.max())
    daily_df = daily_df.reindex(idx, fill_value=0)
    
    # Simple Exponential Smoothing (Holt-Winters)
    # Automatically add trend if we have enough points
    try:
        model = ExponentialSmoothing(
            daily_df[primary_metric] + 0.001, # add small constant to avoid 0s error
            trend='add',
            seasonal='add' if len(daily_df) > 30 else None,
            seasonal_periods=7 if len(daily_df) > 30 else None,
            initialization_method='estimated'
        ).fit()
        
        # Forecast
        forecast = model.forecast(days)
        
        # Test accuracy on last 20%
        split = int(len(daily_df)*0.8)
        train, test = daily_df.iloc[:split], daily_df.iloc[split:]
        if len(test) > 0:
            test_model = ExponentialSmoothing(
                 train[primary_metric] + 0.001, 
                 trend='add', 
                 initialization_method='estimated'
            ).fit()
            preds = test_model.forecast(len(test))
            mae = mean_absolute_error(test[primary_metric], preds)
            rmse = np.sqrt(mean_squared_error(test[primary_metric], preds))
        else:
            mae = 0
            rmse = 0
            
        forecast_dates = pd.date_range(daily_df.index.max() + pd.Timedelta(days=1), periods=days)
        
        # Build JSON response
        result = {
            "historical": {str(k.date()): float(v) for k, v in daily_df[primary_metric].tail(30).items()},
            "forecast": {str(k.date()): float(v) for k, v in zip(forecast_dates, forecast.values)},
            "accuracy": {
                "MAE": float(mae),
                "RMSE": float(rmse)
            }
        }
        return result
    except Exception as e:
        # Fallback if forecasting fails - still return historical data so chart draws
        return {
            "historical": {str(k.date()): float(v) for k, v in daily_df[primary_metric].tail(30).items()},
            "forecast": {},
            "accuracy": {"MAE": 0, "RMSE": 0},
            "warning": str(e)
        }
