import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import get_settings

settings = get_settings()


async def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send email using SMTP"""
    message = MIMEMultipart("alternative")
    message["From"] = settings.from_email
    message["To"] = to_email
    message["Subject"] = subject
    
    # Add text version if provided
    if text_content:
        text_part = MIMEText(text_content, "plain")
        message.attach(text_part)
    
    # Add HTML version
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    # Send email
    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )


async def send_invite_email(to_email: str, team_name: str, inviter_name: str):
    """Send team invitation email"""
    subject = f"You're invited to join {team_name} on Litmer"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #667eea;">Team Invitation</h2>
          <p>Hi there!</p>
          <p><strong>{inviter_name}</strong> has invited you to join the team <strong>{team_name}</strong> on Litmer.</p>
          <p>Litmer is an AI-powered issue tracking platform that helps teams collaborate efficiently.</p>
          <div style="margin: 30px 0;">
            <a href="{settings.frontend_url}/register" 
               style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
              Join Team
            </a>
          </div>
          <p style="color: #666; font-size: 12px;">
            If you already have an account, simply log in and you'll see the team invitation.
          </p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="color: #999; font-size: 11px;">
            This invitation was sent by Litmer on behalf of {inviter_name}.
          </p>
        </div>
      </body>
    </html>
    """
    
    text_content = f"""
    Team Invitation
    
    Hi there!
    
    {inviter_name} has invited you to join the team {team_name} on Litmer.
    
    Litmer is an AI-powered issue tracking platform that helps teams collaborate efficiently.
    
    Join the team: {settings.frontend_url}/register
    
    If you already have an account, simply log in and you'll see the team invitation.
    
    ---
    This invitation was sent by Litmer on behalf of {inviter_name}.
    """
    
    await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, reset_token: str, user_name: str):
    """Send password reset email"""
    subject = "Reset your Litmer password"
    reset_link = f"{settings.frontend_url}/reset-password/{reset_token}"
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #667eea;">Password Reset Request</h2>
          <p>Hi {user_name},</p>
          <p>We received a request to reset your password for your Litmer account.</p>
          <p>Click the button below to reset your password:</p>
          <div style="margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
              Reset Password
            </a>
          </div>
          <p style="color: #666;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_link}" style="color: #667eea;">{reset_link}</a>
          </p>
          <p style="color: #e74c3c; font-size: 14px;">
            <strong>Important:</strong> This link will expire in 1 hour.
          </p>
          <p style="color: #666; font-size: 12px;">
            If you didn't request this password reset, you can safely ignore this email. Your password will not be changed.
          </p>
          <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="color: #999; font-size: 11px;">
            This is an automated email from Litmer. Please do not reply.
          </p>
        </div>
      </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hi {user_name},
    
    We received a request to reset your password for your Litmer account.
    
    Reset your password: {reset_link}
    
    Important: This link will expire in 1 hour.
    
    If you didn't request this password reset, you can safely ignore this email. Your password will not be changed.
    
    ---
    This is an automated email from Litmer. Please do not reply.
    """
    
    await send_email(to_email, subject, html_content, text_content)
