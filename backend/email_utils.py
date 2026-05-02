
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_reset_email(to_email: str, username: str, reset_link: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    email_from = os.getenv("EMAIL_FROM", "").strip()

    if not all([smtp_server, smtp_user, smtp_pass]):
        print("\n[WARNING] SMTP credentials missing in .env. Falling back to terminal link.")
        print(f"[FALLBACK] Reset link for {username}: {reset_link}\n")
        return False

    subject = "Reset your TypeJaldi secret key"
    
    # HTML body with sketch styling (basic)
    html = f"""
    <html>
    <body style="font-family: sans-serif; line-height: 1.6; color: #2c2416; background-color: #fdfaf3; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border: 2px solid #5c4f3a; border-radius: 10px;">
            <h1 style="color: #e8874b; font-size: 24px;">TypeJaldi</h1>
            <p>Hi <strong>{username}</strong>,</p>
            <p>We received a request to reset your password for your TypeJaldi account. Click the button below to set a new one:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #e8874b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reset Password</a>
            </p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            <p style="font-size: 12px; color: #5c4f3a; opacity: 0.6; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
                TypeJaldi - Sharpen your sketch-typing skills.
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        print(f"[FALLBACK] Reset link for {username}: {reset_link}")
        return False
