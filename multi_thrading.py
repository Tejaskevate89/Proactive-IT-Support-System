import threading
import subprocess
import time
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# List of regular Python scripts
regular_scripts = [
    "osinfo.py",
    "ticket.py",
    "predict.py",
    "root.py",
    "mail.py",
    "rei.py",
]

# List of Streamlit scripts
streamlit_scripts = [
    "chart.py",  # First Streamlit app
    "report.py",  # Second Streamlit app
]

def run_script(script_name):
    """Runs a regular Python script in a separate thread."""
    logging.info(f"Starting {script_name}...")
    try:
        subprocess.run(["python", script_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e}")

def run_streamlit_app(script_name, port):
    """Runs a Streamlit app in a separate subprocess."""
    logging.info(f"Starting Streamlit app {script_name} on port {port}...")
    try:
        subprocess.Popen(["streamlit", "run", script_name, "--server.port", str(port)])
    except Exception as e:
        logging.error(f"Error launching Streamlit app {script_name}: {e}")

def main():
    """Main function to run all scripts concurrently."""
    threads = []

    # Start regular Python scripts as threads
    for script in regular_scripts:
        thread = threading.Thread(target=run_script, args=(script,))
        thread.start()
        threads.append(thread)

    # Start Streamlit apps (each on a different port)
    streamlit_ports = [8501, 8502]  # Assign unique ports
    for script, port in zip(streamlit_scripts, streamlit_ports):
        run_streamlit_app(script, port)
        time.sleep(3)  # Small delay to avoid conflicts

    # Wait for all regular script threads to finish
    for thread in threads:
        thread.join()

    logging.info("✅ All scripts have finished execution.")

if __name__ == "__main__":
    main()
