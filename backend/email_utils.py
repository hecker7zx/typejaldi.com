import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def send_reset_email(to_email: str, username: str, reset_link: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "").strip()
    smtp_port   = int(os.getenv("SMTP_PORT", 587))
    smtp_user   = os.getenv("SMTP_USER", "").strip()
    smtp_pass   = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    email_from  = os.getenv("EMAIL_FROM", smtp_user).strip()

    # Always print to terminal as a fallback
    print(f"\n{'='*60}")
    print(f"[PASSWORD RESET] User: {username} | Email: {to_email}")
    print(f"[RESET LINK] {reset_link}")
    print(f"{'='*60}\n")

    if not all([smtp_server, smtp_user, smtp_pass]):
        print("[WARNING] SMTP credentials missing – email not sent, use the link above.\n")
        return False

    subject = "Reset your TypeJaldi password"

    html = f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#c4a484;font-family:'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px;">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#fdfaf3;border:3px solid #5c4f3a;border-radius:12px;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:#e8874b;padding:30px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:32px;letter-spacing:1px;">
              Type<span style="font-style:italic;">Jaldi</span>
            </h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
              ~ sharpen your sketch-typing skills ~
            </p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            <p style="font-size:18px;color:#2c2416;margin:0 0 12px;">Hi <strong>{username}</strong>,</p>
            <p style="font-size:16px;color:#5c4f3a;margin:0 0 28px;line-height:1.6;">
              We received a request to reset the password for your TypeJaldi account.
              Click the button below — the link expires in <strong>1 hour</strong>.
            </p>
            <div style="text-align:center;margin:0 0 28px;">
              <a href="{reset_link}"
                 style="display:inline-block;background:#e8874b;color:#fff;
                        font-size:18px;font-weight:bold;padding:14px 36px;
                        border-radius:10px;text-decoration:none;
                        border-bottom:4px solid #b85d2a;">
                🔑 Reset My Password
              </a>
            </div>
            <p style="font-size:14px;color:#5c4f3a;word-break:break-all;margin:0 0 20px;">
              Or paste this link into your browser:<br>
              <a href="{reset_link}" style="color:#e8874b;">{reset_link}</a>
            </p>
            <hr style="border:none;border-top:1px solid #e0d8c8;margin:24px 0;">
            <p style="font-size:13px;color:#5c4f3a;opacity:0.6;margin:0;">
              If you didn't request this, you can safely ignore this email.
              Your password will not change.
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#2c2416;padding:16px 40px;text-align:center;">
            <p style="margin:0;color:rgba(255,255,255,0.4);font-size:12px;letter-spacing:1px;">
              TYPEJALDI · SKETCH YOUR SPEED
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = email_from
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        print(f"[EMAIL] Connecting to {smtp_server}:{smtp_port} as {smtp_user}...")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, to_email, msg.as_string())
        print(f"[EMAIL] ✅ Reset email sent successfully to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[EMAIL ERROR] Authentication failed: {e}")
        print("[TIP] For Gmail, use an App Password: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"[EMAIL ERROR] {type(e).__name__}: {e}")
        return False
