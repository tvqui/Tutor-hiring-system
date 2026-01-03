# send_email.py
import base64
from email.message import EmailMessage
from email.utils import formataddr
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from zoneinfo import ZoneInfo
import os

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def load_template_with_icon(template_file: str, icon_file: str, context: dict = None):
    """Load HTML template và nhúng icon Base64"""
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    if context:
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

    # Encode icon
    with open(icon_file, "rb") as f:
        encoded_icon = base64.b64encode(f.read()).decode()

    template = template.replace("{{icon_base64}}", encoded_icon)
    return template


def load_template(template_file: str, context: dict = None):
    """Load an HTML template and replace placeholders without an icon"""
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    if context:
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))

    return template


def send_email_v1(recipient: str, subject: str, html_content: str):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        else:
            raise Exception("No valid credentials. Tạo token.json bên ngoài Docker.")

    try:
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message["Subject"] = subject
        message["To"] = recipient
        message["From"] = formataddr((
            "Booking Service",
            service.users().getProfile(userId="me").execute()["emailAddress"],
        ))

        message.set_content("Nếu bạn không xem được HTML, đây là nội dung fallback.")
        message.add_alternative(html_content, subtype="html")

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        service.users().messages().send(userId="me", body=create_message).execute()
        return True

    except HttpError as e:
        print(f"Error sending email: {e}")
        return False


def send_booking_email(
    applicant_email: str,
    applicant_name: str,
    parent_name: str,
    post_title: str,
    poster_email: str,
    poster_phone: str,
    content: str,
):
    template_file = os.path.join(os.path.dirname(__file__), "templates", "booking_template.html")
    icon_file = os.path.join(os.path.dirname(__file__), "assets", "booking-icon.png")

    html_content = load_template_with_icon(
        template_file,
        icon_file,
        context={
            "applicant_name": applicant_name,
            "parent_name": parent_name,
            "post_title": post_title,
            "poster_email": "abc@gmail.com",
            "poster_phone": "123456789",
            "content": content,
        },
    )

    return send_email_v1(applicant_email, "Booking Confirmation", html_content)





def send_parent_notify_email(recipient: str, parent_name: str, post_title: str):
    template_file = os.path.join(os.path.dirname(__file__), "templates", "parent_notify_template.html")
    html_content = load_template(template_file, context={
        "parent_name": parent_name,
        "post_title": post_title,
    })
    return send_email_v1(recipient, "Your post has a tutor", html_content)
