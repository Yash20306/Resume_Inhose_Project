import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.config import settings
from app.services.utils.log import logger


def send_email_smtp(to_email: str, subject: str, body: str):
    """
    Sends an email using configured SMTP server.
    """
    try:
        # 1️⃣ Build the message
        message = MIMEMultipart()
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # 2️⃣ Connect to SMTP
        if settings.SMTP_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)

        # 3️⃣ Login & send
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
        server.quit()

        logger.info(f"✅ Email sent to {to_email} | Subject: {subject}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return False
