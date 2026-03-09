"""Email notification service for user approvals and alerts."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        enabled: bool = False,
    ):
        """
        Initialize email service.

        Args:
            smtp_server: SMTP server address (e.g., 'smtp.gmail.com')
            smtp_port: SMTP port (default 587 for TLS)
            sender_email: From address
            sender_password: SMTP password or app password
            enabled: Whether email sending is enabled
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.enabled = enabled

    def send_approval_notification(self, recipient_email: str, user_name: str):
        """
        Send email notifying user they've been approved.

        Args:
            recipient_email: Email address to send to
            user_name: Name of the approved user
        """
        if not self.enabled:
            logger.warning(f"Email service disabled, skipping approval notification for {recipient_email}")
            return

        subject = "CloudHelm Account Approved"
        body = f"""
        <html>
            <body>
                <h2>Welcome to CloudHelm, {user_name}!</h2>
                <p>Your CloudHelm account has been approved by the administrator.</p>
                <p>You can now access the platform at:</p>
                <p><a href="https://joao19921.github.io/CloudHelm">https://joao19921.github.io/CloudHelm</a></p>
                <p>If you have any questions, please contact your administrator.</p>
                <hr>
                <p><em>CloudHelm - Cloud Architecture Control Plane</em></p>
            </body>
        </html>
        """
        self._send_email(recipient_email, subject, body)

    def send_access_revoked_notification(self, recipient_email: str, user_name: str, reason: Optional[str] = None):
        """
        Send email notifying user their access has been revoked.

        Args:
            recipient_email: Email address to send to
            user_name: Name of the user
            reason: Optional reason for revocation
        """
        if not self.enabled:
            logger.warning(f"Email service disabled, skipping revocation notification for {recipient_email}")
            return

        subject = "CloudHelm Access Revoked"
        reason_text = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        body = f"""
        <html>
            <body>
                <h2>CloudHelm Access Revoked</h2>
                <p>Hello {user_name},</p>
                <p>Your access to CloudHelm has been revoked.</p>
                {reason_text}
                <p>If you believe this is a mistake, please contact your administrator.</p>
                <hr>
                <p><em>CloudHelm - Cloud Architecture Control Plane</em></p>
            </body>
        </html>
        """
        self._send_email(recipient_email, subject, body)

    def send_access_expiration_notice(self, recipient_email: str, user_name: str, expires_at: str):
        """
        Send email warning user that their access is expiring soon.

        Args:
            recipient_email: Email address to send to
            user_name: Name of the user
            expires_at: When the access expires (ISO format string)
        """
        if not self.enabled:
            logger.warning(f"Email service disabled, skipping expiration notice for {recipient_email}")
            return

        subject = "CloudHelm Access Expiring Soon"
        body = f"""
        <html>
            <body>
                <h2>Access Expiration Notice</h2>
                <p>Hello {user_name},</p>
                <p>Your CloudHelm access will expire on <strong>{expires_at}</strong>.</p>
                <p>If you need extended access, please contact your administrator.</p>
                <hr>
                <p><em>CloudHelm - Cloud Architecture Control Plane</em></p>
            </body>
        </html>
        """
        self._send_email(recipient_email, subject, body)

    def send_role_change_notification(self, recipient_email: str, user_name: str, new_role: str):
        """
        Send email notifying user their role has changed.

        Args:
            recipient_email: Email address to send to
            user_name: Name of the user
            new_role: New role name
        """
        if not self.enabled:
            logger.warning(f"Email service disabled, skipping role change notification for {recipient_email}")
            return

        subject = "CloudHelm Role Updated"
        role_description = {
            "admin": "Administrator (full access)",
            "reviewer": "Reviewer (can approve users)",
            "user": "User (standard access)",
        }.get(new_role, new_role)

        body = f"""
        <html>
            <body>
                <h2>Role Update</h2>
                <p>Hello {user_name},</p>
                <p>Your CloudHelm role has been updated to: <strong>{role_description}</strong></p>
                <p>This change affects what you can do in the platform.</p>
                <hr>
                <p><em>CloudHelm - Cloud Architecture Control Plane</em></p>
            </body>
        </html>
        """
        self._send_email(recipient_email, subject, body)

    def _send_email(self, recipient: str, subject: str, html_body: str):
        """
        Internal method to send an email.

        Args:
            recipient: Email address to send to
            subject: Email subject
            html_body: HTML email body
        """
        if not self.enabled or not self.smtp_server:
            logger.warning("Email service not fully configured")
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient

            # Attach HTML body
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"Email sent to {recipient}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")


# Global email service instance (initialized in main.py)
email_service: Optional[EmailService] = None


def init_email_service(
    smtp_server: Optional[str] = None,
    smtp_port: int = 587,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
) -> EmailService:
    """Initialize the global email service."""
    global email_service
    email_service = EmailService(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        sender_password=sender_password,
        enabled=bool(smtp_server and sender_email and sender_password),
    )
    return email_service


def get_email_service() -> Optional[EmailService]:
    """Get the global email service instance."""
    return email_service
