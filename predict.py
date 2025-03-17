import pymongo  # MongoDB library for interacting with the database
from datetime import datetime, timezone  # For working with dates and times
import logging  # To log messages for debugging
import os  # For managing file paths and directories
import numpy as np  # For numerical operations, like creating arrays
from sklearn.linear_model import LinearRegression  # For building a machine learning model

# MongoDB Setup: Connect to the MongoDB database where we store system data
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]  # Database name
system_stats_collection = db["system_stats"]  # Collection (table) for system data
predictions_collection = db["predictions"]  # New collection to store predictions

# Log File Setup: This will save log messages to a file for tracking
log_file_path = "../logs/predict.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)  # Create the log directory if it doesn't exist

# Set up logging to save debug information in the log file
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Cache to store fetched data (temporary storage to avoid repeated database queries)
data_cache = {
    "cpu_usage": [],  # For storing CPU usage data
    "memory_percent": [],  # For storing memory usage data
    "disk_percent": []  # For storing disk usage data
}

# Debug log function: Prints and logs messages for debugging
def debug_log(message):
    """Log debug messages."""
    print(f"[DEBUG] {message}")
    logging.debug(message)

# Function to fetch and cache the last 'limit' records for a specific metric (like cpu_usage, memory_percent)
def fetch_and_cache_data(metric, limit=50):
    """Fetch the last 'limit' records for a specific metric and cache it."""
    try:
        debug_log(f"Fetching the last {limit} records for {metric}")
        
        # Fetch the last 'limit' records from MongoDB, sorted by timestamp (newest first)
        data = system_stats_collection.find(
            {},  # No filter, fetch all records
            {"timestamp": 1, metric: 1}  # Only include the timestamp and the specified metric
        ).sort("timestamp", pymongo.DESCENDING).limit(limit)
        
        # Extract the metric values and store them in the cache
        metric_values = [record.get(metric) for record in data]
        data_cache[metric] = metric_values
        
        debug_log(f"Fetched and cached {len(metric_values)} records for {metric}")
        
    except Exception as e:
        logging.error(f"Error fetching and caching data for {metric}: {e}")
        debug_log(f"Error fetching and caching data for {metric}: {e}")

# Function to train a machine learning model (linear regression) using the fetched data
def train_prediction_model(data):
    """Train a linear regression model using the provided data."""
    try:
        debug_log("Training prediction model...")
        # Prepare the data (timestamps as time and the metric values as target)
        timestamps = np.array([i for i in range(len(data))]).reshape(-1, 1)  # Convert index to time in seconds
        values = np.array(data)  # Metric values (like cpu usage, memory percent, etc.)
        
        # Create and train a linear regression model
        model = LinearRegression()
        model.fit(timestamps, values)
        
        debug_log("Model trained successfully.")
        return model
    except Exception as e:
        logging.error(f"Error training the model: {e}")
        debug_log(f"Error training the model: {e}")

# Function to predict future values using the trained model for various time intervals (in seconds)
def predict_future_values(model, start_index, time_intervals=[10, 60, 300, 600, 1440]):
    """Predict future values for given time intervals (in seconds)."""
    try:
        debug_log(f"Predicting future values for the next {time_intervals} seconds...")
        predictions = {}
        for interval in time_intervals:
            future_index = start_index + interval  # Calculate the future time index (current + interval)
            predicted_value = model.predict([[future_index]])  # Predict the value for the future time
            predictions[str(interval)] = predicted_value[0]  # Convert interval to string for MongoDB key
        
        debug_log(f"Predicted values: {predictions}")
        return predictions
    except Exception as e:
        logging.error(f"Error predicting future values: {e}")
        debug_log(f"Error predicting future values: {e}")

# Function to save predictions to MongoDB
def save_predictions_to_mongo(metric, predictions):
    """Save the predicted values to the MongoDB 'predictions' collection."""
    try:
        debug_log(f"Saving predictions for {metric} to MongoDB...")
        # Create a document to store the prediction results
        prediction_data = {
            "metric": metric,
            "timestamp": datetime.now(timezone.utc),  # Current timestamp when the prediction is made
            "predictions": predictions  # Store all the predictions in one document
        }
        
        # Insert the prediction document into the MongoDB collection
        predictions_collection.insert_one(prediction_data)
        
        debug_log(f"Saved predictions for {metric} to MongoDB.")
    except Exception as e:
        logging.error(f"Error saving predictions to MongoDB for {metric}: {e}")
        debug_log(f"Error saving predictions to MongoDB for {metric}: {e}")

# Function to print the cached data for debugging
def print_cached_data():
    """Print the cached data arrays for each feature."""
    for metric, values in data_cache.items():
        debug_log(f"Cached data for {metric}:")
        print(f"{metric} values: {values}")

# Function to apply machine learning to each metric and predict future values
def apply_machine_learning():
    """Apply machine learning to predict future values and save them to MongoDB."""
    for metric, data in data_cache.items():
        if len(data) > 1:  # Ensure we have enough data to train the model
            debug_log(f"Training model for {metric}...")
            model = train_prediction_model(data)  # Train the model
            
            # Predict future values for the next 10 minutes, 1 hour, 5 hours, etc.
            predictions = predict_future_values(model, start_index=len(data)-1)
            
            # Print the predictions in a user-friendly format
            debug_log(f"Predictions for {metric}: {predictions}")
            print(f"\n--- Predictions for {metric} ---")
            for interval, predicted_value in predictions.items():
                print(f"In the next {interval} seconds, the predicted {metric} is: {predicted_value:.2f}")
                
            # Save predictions to MongoDB
            save_predictions_to_mongo(metric, predictions)
        else:
            debug_log(f"Not enough data to train model for {metric}")

def main():
    """
    Main function to fetch data, train models, make predictions, and store results in MongoDB.
    """
    debug_log("Starting the prediction script...")

    # Fetch the last 50 records for CPU, memory, and disk usage and store them in the cache
    debug_log("Fetching and caching system data...")
    fetch_and_cache_data("cpu_usage", limit=50)
    fetch_and_cache_data("memory_percent", limit=50)
    fetch_and_cache_data("disk_percent", limit=50)

    # Print the fetched data for debugging
    debug_log("Printing cached data...")
    print_cached_data()

    # Apply machine learning models to make predictions and save them to MongoDB
    debug_log("Applying machine learning to generate predictions...")
    apply_machine_learning()

    debug_log("Prediction script completed successfully.")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
