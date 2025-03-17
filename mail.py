import smtplib
import pymongo
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

# MongoDB Connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["rootsense"]

# Collections
system_stats_collection = db["system_stats"]
predictions_collection = db["predictions"]
root_cause_collection = db["root_cause"]
rei_collection = db["rei"]

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"  # Change for Outlook, Yahoo, etc.
SMTP_PORT = 587
EMAIL_SENDER = "yarnalkaramey@gmail.com"  # Update your email
EMAIL_PASSWORD = "pkjgoxrbnipawuwx"  # Use an App Password for security
EMAIL_RECEIVER = "yarnalkaramey@gmail.com"  # Update recipient email

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_latest_data(collection, sort_field="timestamp"):
    """Fetch the latest document from the given MongoDB collection."""
    try:
        return collection.find_one({}, sort=[(sort_field, -1)])
    except Exception as e:
        logging.error(f"Error fetching data from {collection.name}: {e}")
        return None

def format_email_summary():
    """Generate the email summary from database records."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Fetch latest data
    system_stats = fetch_latest_data(system_stats_collection)
    predictions = fetch_latest_data(predictions_collection)
    root_cause = fetch_latest_data(root_cause_collection)
    rei_summary = fetch_latest_data(rei_collection)

    # Greeting
    email_body = f"""
    <html>
    <body>
        <h2>Hello Team,</h2>
        <p>Here is the latest system performance summary as of <strong>{timestamp}</strong>:</p>
        
        <h3>🔹 System Metrics Summary:</h3>
        <ul>
    """

    # System Stats Summary
    if system_stats:
        for key, value in system_stats.items():
            if key not in ["_id", "timestamp"]:
                email_body += f"<li><strong>{key}:</strong> {value}</li>"
    else:
        email_body += "<li>No system metrics available.</li>"
    
    email_body += "</ul><h3>🔹 Prediction Summary:</h3><ul>"

    # Predictions Summary
    if predictions:
        for key, value in predictions.items():
            if key not in ["_id", "timestamp"]:
                email_body += f"<li><strong>{key}:</strong> Predicted {value}</li>"
    else:
        email_body += "<li>No predictions available.</li>"

    email_body += "</ul><h3>🔹 Root Cause Analysis:</h3><ul>"

    # Root Cause Analysis
    if root_cause:
        for key, value in root_cause.items():
            if key not in ["_id", "timestamp"]:
                email_body += f"<li><strong>{key}:</strong> {value}</li>"
    else:
        email_body += "<li>No root cause analysis data available.</li>"

    email_body += "</ul><h3>🔹 Resource Efficiency Index (REI) Summary:</h3><ul>"

    # REI Summary
    if rei_summary:
        email_body += f"""
        <li><strong>Overall REI:</strong> {rei_summary.get('overall_rei', 'N/A')}%</li>
        <li><strong>Insight:</strong> {rei_summary.get('overall_insight', 'No insight available.')}</li>
        """
    else:
        email_body += "<li>No REI data available.</li>"

    # Final Conclusion
    email_body += """
        </ul>
        <h3>✅ Conclusion:</h3>
        <p>The system is operating based on the analyzed metrics. Please review the insights and take necessary actions if required.</p>
        <p>Best Regards,<br><strong>RootSense Monitoring System</strong></p>
    </body>
    </html>
    """

    return email_body

def send_email():
    """Sends an email with the summary report."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = "📊 RootSense: System Performance Summary"

        # Attach the formatted email body
        msg.attach(MIMEText(format_email_summary(), "html"))

        # SMTP Connection
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        logging.info("Summary email sent successfully.")
        print("✅ Email Sent Successfully!")

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        print(f"❌ Failed to send email: {e}")

def main():
    """Main function to execute email sending."""
    send_email()

if __name__ == "__main__":
    main()
