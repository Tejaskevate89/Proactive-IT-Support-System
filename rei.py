import pymongo
import logging
import os
from datetime import datetime, timezone

# MongoDB Setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]

# Collections
system_stats_collection = db["system_stats"]
predictions_collection = db["predictions"]
rei_collection = db["rei"]

# Log File Setup
log_file_path = "../logs/system_logs.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def fetch_system_stats():
    """Fetch all system stats data."""
    try:
        return list(system_stats_collection.find())
    except Exception as e:
        logging.error(f"Error fetching system stats: {e}")
        return []

def fetch_predictions():
    """Fetch all predictions data."""
    try:
        return list(predictions_collection.find())
    except Exception as e:
        logging.error(f"Error fetching predictions: {e}")
        return []

def calculate_rei(actual_usage, predicted_usage):
    """Calculate Resource Efficiency Index (REI)."""
    try:
        if predicted_usage > 0:
            return round((actual_usage / predicted_usage) * 100, 2)
    except Exception as e:
        logging.error(f"Error calculating REI: {e}")
    return None

def get_rei_insights(rei):
    """Generate insights based on REI."""
    if rei > 100:
        return "The system is highly efficient. Resources are under-utilized."
    elif 80 <= rei <= 100:
        return "The system is operating efficiently. Resources are being used optimally."
    elif 50 <= rei < 80:
        return "The system is somewhat inefficient. There is room for improvement in resource utilization."
    return "The system is inefficient. Consider optimizing resource usage and processes."

def calculate_and_display_rei():
    """Calculate REI for each metric and overall REI."""
    system_stats = fetch_system_stats()
    predictions_data = fetch_predictions()

    if not system_stats or not predictions_data:
        print("No sufficient data found for REI calculation.")
        return

    total_rei = 0
    metric_count = 0

    print("\nResource Efficiency Index (REI) Calculation:")
    for stat in system_stats:
        print(f"\nTimestamp: {stat.get('timestamp')}")
        for metric, actual_usage in stat.items():
            if metric not in ["cpu_usage", "memory_percent", "disk_percent"]:
                continue  # Skip metrics that don't have predictions

            # Find the corresponding prediction data
            predicted_entry = next(
                (pred for pred in predictions_data if pred["metric"] == metric), None
            )
            if not predicted_entry or "predictions" not in predicted_entry:
                print(f"No prediction data found for {metric}.")
                logging.warning(f"No prediction data found for {metric}.")
                continue

            # Use the closest prediction (e.g., 10-minute interval for simplicity)
            predictions = predicted_entry["predictions"]
            predicted_usage = predictions.get("10")  # Change interval as needed

            rei = calculate_rei(actual_usage, predicted_usage)
            if rei is not None:
                total_rei += rei
                metric_count += 1
                insight = get_rei_insights(rei)
                print(f"{metric} REI: {rei}% - {insight}")
                logging.info(f"{metric}: REI {rei}% (Actual: {actual_usage}, Predicted: {predicted_usage})")
            else:
                print(f"Error calculating REI for {metric}.")
                logging.error(f"Error calculating REI for {metric}.")

    if metric_count > 0:
        overall_rei = total_rei / metric_count
        overall_insight = get_rei_insights(overall_rei)
        print(f"\nOverall Resource Efficiency Index (REI): {overall_rei}%")
        print(overall_insight)

        # Save the overall REI and insights to MongoDB
        try:
            rei_data = {
                "timestamp": datetime.now(timezone.utc),
                "overall_rei": overall_rei,
                "overall_insight": overall_insight,
            }
            rei_collection.insert_one(rei_data)
            logging.info("Saved overall REI and insights to the database.")
        except Exception as e:
            logging.error(f"Error saving overall REI: {e}")
    else:
        print("No valid metrics to calculate the overall REI.")

def main():
    """Main function to initiate the REI calculation."""
    print("Starting the Resource Efficiency Index (REI) Calculation:")
    logging.info("Starting REI Calculation.")
    try:
        calculate_and_display_rei()
        logging.info("REI Calculation completed successfully.")
    except Exception as e:
        logging.error(f"Error during REI Calculation: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
