"""
Email Utility for EverNothing
Sends password reset emails via AWS SES or SMTP

Configuration (environment variables):
- EMAIL_BACKEND: 'ses' or 'smtp' (default: 'ses')
- AWS_SES_REGION: AWS region for SES (default: 'us-east-1')
- SMTP_HOST: SMTP server hostname
- SMTP_PORT: SMTP server port (default: 587)
- SMTP_USER: SMTP username
- SMTP_PASS: SMTP password
- EMAIL_FROM: Sender email address
"""

import os
import logging

logger = logging.getLogger(__name__)

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'ses')
AWS_SES_REGION = os.environ.get('AWS_SES_REGION', 'us-east-1')
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@evernothing.com')

def send_password_reset_email(to_email, reset_link):
    """Send password reset email to user"""
    subject = "EverNothing - Password Reset Request"
    body_text = f"""
Hello,

You requested a password reset for your EverNothing account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
EverNothing Team
"""
    
    body_html = f"""
<html>
<head></head>
<body style="background-color: black; color: gold; font-family: sans-serif;">
  <h2 style="color: gold;">EverNothing - Password Reset</h2>
  <p>You requested a password reset for your EverNothing account.</p>
  <p>Click the link below to reset your password:</p>
  <p><a href="{reset_link}" style="color: red; font-weight: bold;">{reset_link}</a></p>
  <p style="color: #888;">This link will expire in 1 hour.</p>
  <p>If you did not request this reset, please ignore this email.</p>
  <hr style="border-color: red;">
  <p style="font-size: small;">Best regards,<br>EverNothing Team</p>
</body>
</html>
"""
    
    if EMAIL_BACKEND == 'ses':
        return send_via_ses(to_email, subject, body_text, body_html)
    else:
        return send_via_smtp(to_email, subject, body_text, body_html)

def send_via_ses(to_email, subject, body_text, body_html):
    """Send email via AWS SES"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        client = boto3.client('ses', region_name=AWS_SES_REGION)
        
        response = client.send_email(
            Source=EMAIL_FROM,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            }
        )
        logger.info(f"Password reset email sent to {to_email} via SES: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"SES email error: {e.response['Error']['Message']}")
        return False
    except ImportError:
        logger.error("boto3 not installed, cannot send via SES")
        return False
    except Exception as e:
        logger.error(f"Failed to send email via SES: {e}")
        return False

def send_via_smtp(to_email, subject, body_text, body_html):
    """Send email via SMTP"""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        
        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(body_html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        
        logger.info(f"Password reset email sent to {to_email} via SMTP")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
        return False
