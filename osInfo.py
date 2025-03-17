import psutil
import time
from pymongo import MongoClient
from datetime import datetime
import logging
import os
import argparse

# Configure logging with a configurable log level
def configure_logging():
    # Ensure the log directory exists
    log_dir = "../logs/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Parse log level from command-line arguments
    parser = argparse.ArgumentParser(description="Configure log level.")
    parser.add_argument("--log-level", type=str, default="DEBUG", help="Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser.parse_args()

    # Resolve the log level
    log_level = getattr(logging, args.log_level.upper(), logging.DEBUG)

    # Clear existing handlers and configure logging
    logging.getLogger().handlers.clear()

    logging.basicConfig(
        filename=os.path.join(log_dir, "os_data.log"),
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Add console logging for immediate feedback
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(console)

    logging.info("Logging configured with level: %s", args.log_level.upper())

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI if needed
    db = client["rootsense"]  # Database name
    collection = db["system_stats"]  # Collection name
    logging.info("Connected to MongoDB successfully.")
except Exception as e:
    logging.error("Failed to connect to MongoDB: %s", e)
    raise

def get_system_data():
    """
    Fetches the system data such as CPU, memory, disk, and network statistics.
    Returns:
        dict: A dictionary containing the system metrics.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage over 1 second
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        system_data = {
            "timestamp": datetime.now(),
            "cpu_usage": cpu_usage,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_free": memory.free,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "disk_percent": disk.percent,
            "network_sent": network.bytes_sent,
            "network_recv": network.bytes_recv
        }

        logging.debug("System data fetched: %s", system_data)
        return system_data
    except Exception as e:
        logging.error("Error fetching system data: %s", e)
        raise

def store_data_in_mongodb(data_batch):
    """
    Inserts a batch of system data into MongoDB.
    Args:
        data_batch (list): A list of system metrics to be stored.
    """
    try:
        if data_batch:
            collection.insert_many(data_batch)
            logging.info("Batch of %d records inserted into MongoDB.", len(data_batch))
    except Exception as e:
        logging.error("Error inserting batch data into MongoDB: %s", e)
        raise

def main():
    """
    Main function to periodically fetch system data and store it in MongoDB.
    """
    logging.info("Starting system data monitoring...")
    data_batch = []
    try:
        while True:
            system_data = get_system_data()  # Get system metrics
            data_batch.append(system_data)

            # Insert data in batches of 10
            if len(data_batch) >= 10:
                store_data_in_mongodb(data_batch)
                data_batch.clear()

            time.sleep(5)  # Wait for 5 seconds before the next fetch
    except KeyboardInterrupt:
        logging.info("System data monitoring stopped by user.")
        if data_batch:
            logging.info("Inserting remaining data before shutdown.")
            store_data_in_mongodb(data_batch)
    except Exception as e:
        logging.error("Unexpected error in main loop: %s", e)

if __name__ == "__main__":
    configure_logging()
    main()
