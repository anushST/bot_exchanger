import aiosmtplib
from email.message import EmailMessage

from src.core.config import settings

SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
EMAIL_SENDER = settings.SMTP_EMAIL
EMAIL_PASSWORD = settings.SMTP_EMAIL_PASSWORD


async def send_mail(recipient: str, subject: str, body: str):
    msg = EmailMessage()
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
        )
        print(f'Email sent to {recipient}')
    except Exception as e:
        print(f'Error sending email: {e}')
