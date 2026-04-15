import smtplib
import json
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def send_alert(event_type: str, track_id: int, evidence_path: str, config_path: str = 'config.json'):
    """Send email alert with image (safe version - no crash)"""

    try:
        # Load config
        with open(config_path, 'r') as f:
            config = json.load(f)

        email_config = config.get('email', {})

        sender = email_config.get('sender_email')
        password = email_config.get('sender_password')
        receiver = email_config.get('receiver_email')

        # Validate config
        if not sender or not password or not receiver:
            print("⚠️ Email config missing")
            return

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"🚨 ALERT: {event_type.upper()} (ID {track_id})"

        # Email body
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        body = f"""
🚨 Surveillance Alert

Event Type : {event_type}
Person ID  : {track_id}
Time       : {ts}

System detected suspicious activity.
        """

        msg.attach(MIMEText(body, 'plain'))

        # Attach image safely
        if evidence_path and os.path.exists(evidence_path):
            try:
                with open(evidence_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(evidence_path)
                    )
                    msg.attach(img)
            except Exception as e:
                print(f"⚠️ Image attach failed: {e}")
        else:
            print("⚠️ Evidence image not found")

        # Connect to SMTP
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()

        # Login (IMPORTANT: use APP PASSWORD)
        server.login(sender, password)

        # Send mail
        server.send_message(msg)
        server.quit()

        print(f"✅ Email sent: {event_type} | ID {track_id}")

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail Authentication Failed → Use APP PASSWORD (NOT normal password)")

    except Exception as e:
        print(f"❌ Email Error: {e}")