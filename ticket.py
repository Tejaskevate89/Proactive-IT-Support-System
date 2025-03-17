import pymongo
from datetime import datetime, timezone
import logging
import os
import time

# Debugging Mode
DEBUG = True  # Set to `False` in production

# MongoDB Setup
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]
system_stats_collection = db["system_stats"]
tickets_collection = db["tickets"]

# Thresholds
THRESHOLDS = {
    "cpu": 1,  # CPU usage threshold (%)
    "memory": 75.0,  # Memory usage threshold (%)
    "disk": 80.0,  # Disk usage threshold (%)
}

# Log File Setup
log_file_path = "../logs/ticket.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def debug_log(message):
    """Log debug messages if DEBUG mode is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}")
    logging.debug(message)

def ensure_log_file():
    """Ensure the log file exists and print a message to the console."""
    if not os.path.isfile(log_file_path):
        debug_log(f"Log file {log_file_path} does not exist. Creating it.")
        open(log_file_path, 'w').close()
    debug_log(f"Logging to file: {log_file_path}")

def get_system_data():
    """Fetch the latest system data from MongoDB."""
    try:
        debug_log("Attempting to fetch the latest system data from MongoDB.")
        latest_data = system_stats_collection.find().sort("timestamp", pymongo.DESCENDING).limit(1)
        data_list = list(latest_data)
        if data_list:
            debug_log(f"Fetched data: {data_list[0]}")
            return data_list[0]
        else:
            logging.warning("No system data available in the 'system_stats' collection.")
            return None
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        if DEBUG:
            raise e
        return None

def generate_ticket(metric, value, threshold, log_message):
    """Generate a ticket for a threshold breach."""
    debug_log(f"Generating ticket for {metric}: {value} exceeded {threshold}")
    ticket = {
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "timestamp": datetime.now(timezone.utc),
        "status": "Open",
        "logs": log_message,
    }
    debug_log(f"Generated ticket: {ticket}")
    return ticket

def monitor_resources():
    """Monitor resources and generate tickets if thresholds are exceeded."""
    ensure_log_file()

    try:
        while True:
            debug_log("Monitoring system resources...")
            data = get_system_data()
            if not data:
                debug_log("No data found; retrying after 10 seconds.")
                time.sleep(10)
                continue

            tickets = []

            # Check thresholds
            cpu_usage = data.get("cpu_usage", 0.0)
            memory_percent = data.get("memory_percent", 0.0)
            disk_percent = data.get("disk_percent", 0.0)

            debug_log(f"CPU: {cpu_usage}, Memory: {memory_percent}, Disk: {disk_percent}")
            debug_log(f"Thresholds - CPU: {THRESHOLDS['cpu']}, Memory: {THRESHOLDS['memory']}, Disk: {THRESHOLDS['disk']}")

            if cpu_usage > THRESHOLDS["cpu"]:
                log_message = f"CPU usage {cpu_usage}% exceeded threshold {THRESHOLDS['cpu']}%"
                logging.warning(log_message)
                tickets.append(generate_ticket("CPU", cpu_usage, THRESHOLDS["cpu"], log_message))

            if memory_percent > THRESHOLDS["memory"]:
                log_message = f"Memory usage {memory_percent}% exceeded threshold {THRESHOLDS['memory']}%"
                logging.warning(log_message)
                tickets.append(generate_ticket("Memory", memory_percent, THRESHOLDS["memory"], log_message))

            if disk_percent > THRESHOLDS["disk"]:
                log_message = f"Disk usage {disk_percent}% exceeded threshold {THRESHOLDS['disk']}%"
                logging.warning(log_message)
                tickets.append(generate_ticket("Disk", disk_percent, THRESHOLDS["disk"], log_message))

            # Save tickets to MongoDB
            try:
                if tickets:
                    result = tickets_collection.insert_many(tickets)
                    debug_log(f"Inserted ticket IDs: {result.inserted_ids}")
                    logging.info(f"{len(tickets)} tickets saved to MongoDB.")
                else:
                    debug_log("No tickets generated; no insertion to MongoDB.")
            except Exception as e:
                logging.error(f"Error inserting tickets into MongoDB: {e}")
                debug_log(f"Exception during ticket insertion: {e}")

            # Debug log the fetched data
            debug_log(f"Latest fetched system data: {data}")

            # Wait before next iteration
            debug_log("Sleeping for 10 seconds before the next check.")
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
        debug_log("Exiting monitoring loop due to user interruption.")
    except Exception as e:
        logging.error(f"Unexpected error in monitoring loop: {e}")
        debug_log(f"Unexpected error: {e}")

def main():
    """Main function to start the monitoring script."""
    debug_log("Starting the resource monitoring script.")
    monitor_resources()

# Run the script
if __name__ == "__main__":
    main()
