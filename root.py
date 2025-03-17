import pymongo
import logging
import os
import pandas as pd
from datetime import datetime, timezone
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import numpy as np

# MongoDB Setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]
system_stats_collection = db["system_stats"]

# Log File Setup
log_file_path = "../logs/root.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Cache to store fetched data
data_cache = {
    "cpu_usage": [],
    "memory_percent": [],
    "disk_percent": []
}

def debug_log(message):
    """Log debug messages."""
    print(f"[DEBUG] {message}")
    logging.debug(message)

def fetch_and_cache_data(metric, limit=50):
    """Fetch the last 'limit' records for a specific metric and cache it."""
    try:
        debug_log(f"Fetching the last {limit} records for {metric}...")
        
        # Fetch the last 'limit' records from MongoDB sorted by timestamp (descending)
        data = system_stats_collection.find(
            {},  # No filter, fetch all records
            {"timestamp": 1, metric: 1}  # Only include timestamp and the specified metric
        ).sort("timestamp", pymongo.DESCENDING).limit(limit)
        
        # Extract the metric values and cache them
        metric_values = [record.get(metric) for record in data]
        data_cache[metric] = metric_values
        
        debug_log(f"Fetched and cached {len(metric_values)} records for {metric}.")
        
        if len(metric_values) < 2:
            debug_log(f"Warning: Not enough data to perform analysis for {metric}.")
        
    except Exception as e:
        logging.error(f"Error fetching and caching data: {e}")
        debug_log(f"Error fetching and caching data: {e}")

def hypothesis_testing():
    """Test hypotheses using statistical methods."""
    try:
        if len(data_cache["cpu_usage"]) < 2 or len(data_cache["memory_percent"]) < 2:
            debug_log("Not enough data for hypothesis testing. Skipping hypothesis testing.")
            return
        
        debug_log("Testing hypothesis: Correlation between CPU and Memory Usage...")
        
        # Perform correlation test for cpu_usage and memory_percent
        cpu_memory_corr, _ = stats.pearsonr(data_cache["cpu_usage"], data_cache["memory_percent"])
        debug_log(f"Correlation between CPU and Memory usage: {cpu_memory_corr:.2f}")
        
        # Hypothesis Test: Check if correlation is statistically significant
        t_stat, p_value = stats.ttest_ind(data_cache["cpu_usage"], data_cache["memory_percent"])
        debug_log(f"T-statistic: {t_stat:.2f}, P-value: {p_value:.4f}")
        
        # If p-value is below 0.05, correlation is statistically significant
        if p_value < 0.05:
            debug_log("The correlation between CPU and Memory usage is statistically significant.")
        else:
            debug_log("The correlation between CPU and Memory usage is not statistically significant.")
            
    except Exception as e:
        logging.error(f"Error in hypothesis testing: {e}")
        debug_log(f"Error in hypothesis testing: {e}")

def train_predictive_model():
    """Train a predictive model to forecast future issues."""
    try:
        if len(data_cache["cpu_usage"]) < 2 or len(data_cache["memory_percent"]) < 2 or len(data_cache["disk_percent"]) < 2:
            debug_log("Not enough data to train the model. Skipping model training.")
            return None
        
        debug_log("Training predictive model to forecast disk usage...")
        
        # Prepare data for model training
        data = pd.DataFrame({
            'cpu_usage': data_cache["cpu_usage"],
            'memory_percent': data_cache["memory_percent"],
            'disk_percent': data_cache["disk_percent"]
        })
        
        # Feature engineering: Lag values (previous time points)
        data['cpu_usage_lag1'] = data['cpu_usage'].shift(1)
        data['memory_percent_lag1'] = data['memory_percent'].shift(1)
        data['disk_percent_lag1'] = data['disk_percent'].shift(1)
        
        data = data.dropna()  # Drop missing values due to lag features
        
        if len(data) < 2:
            debug_log("Not enough data after feature engineering for model training.")
            return None
        
        # Define features and target
        X = data[['cpu_usage_lag1', 'memory_percent_lag1', 'disk_percent_lag1']]
        y = data['disk_percent']  # Predicting disk_percent
        
        # Train a Random Forest Model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Make predictions on the training data
        predictions = model.predict(X)
        mae = mean_absolute_error(y, predictions)
        
        debug_log(f"Model trained. Mean Absolute Error for prediction: {mae:.2f}")
        
        return model
        
    except Exception as e:
        logging.error(f"Error in training predictive model: {e}")
        debug_log(f"Error in training predictive model: {e}")
        return None

def predict_future(model, future_hours=24):
    """Predict future disk usage for the given number of hours."""
    try:
        if model is None:
            debug_log("Model is not trained. Skipping prediction.")
            return
        
        debug_log(f"Predicting future disk usage for the next {future_hours} hour(s)...")
        
        # Prepare input data for prediction (using the latest record for prediction)
        latest_data = pd.DataFrame({
            'cpu_usage_lag1': [data_cache["cpu_usage"][-1]],
            'memory_percent_lag1': [data_cache["memory_percent"][-1]],
            'disk_percent_lag1': [data_cache["disk_percent"][-1]]
        })
        
        # Make predictions for the next hours
        predicted_values = model.predict(latest_data)
        
        debug_log(f"Predicted disk usage for the next {future_hours} hour(s): {predicted_values[0]:.2f}")
        
        return predicted_values[0]
        
    except Exception as e:
        logging.error(f"Error in prediction: {e}")
        debug_log(f"Error in prediction: {e}")

def save_predictions_to_root(predictions):
    """Save the predictions to the root collection in MongoDB."""
    try:
        if predictions is None:
            debug_log("No predictions to save. Skipping MongoDB saving.")
            return
        
        debug_log("Saving predictions to the root collection in MongoDB...")
        
        # Create a dictionary to store predictions
        prediction_data = {
            "timestamp": datetime.now(timezone.utc),
            "cpu_usage_predictions": predictions.get("cpu_usage", None),
            "memory_percent_predictions": predictions.get("memory_percent", None),
            "disk_percent_predictions": predictions.get("disk_percent", None),
        }
        
        # Save to MongoDB root collection
        result = db["rootsense"].insert_one(prediction_data)
        debug_log(f"Predictions saved to MongoDB with id: {result.inserted_id}")
        
    except Exception as e:
        logging.error(f"Error saving predictions to MongoDB: {e}")
        debug_log(f"Error saving predictions to MongoDB: {e}")

def main():
    """Main function to execute the workflow."""
    debug_log("Starting the prediction workflow...")
    
    # Fetch and cache data
    fetch_and_cache_data("cpu_usage", limit=50)
    fetch_and_cache_data("memory_percent", limit=50)
    fetch_and_cache_data("disk_percent", limit=50)
    
    # Perform hypothesis testing
    hypothesis_testing()
    
    # Train predictive models
    cpu_model = train_predictive_model()
    memory_model = train_predictive_model()
    disk_model = train_predictive_model()
    
    # Make predictions
    cpu_predictions = predict_future(cpu_model, future_hours=24)
    memory_predictions = predict_future(memory_model, future_hours=24)
    disk_predictions = predict_future(disk_model, future_hours=24)
    
    # Aggregate predictions
    predictions = {
        "cpu_usage": cpu_predictions,
        "memory_percent": memory_predictions,
        "disk_percent": disk_predictions
    }
    
    # Save predictions to MongoDB
    save_predictions_to_root(predictions)
    
    debug_log("Prediction workflow completed successfully.")

if __name__ == "__main__":
    main()
