import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException
from app.config.config import settings
from app.repository.user_repository import UserRepository


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    # -------------------- PASSWORD UTILS --------------------
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify raw password against its hash."""
        return pwd_context.verify(password, hashed_password)

    # -------------------- TOKEN UTILS --------------------
    @staticmethod
    def create_token(data: dict, expires_delta: timedelta = timedelta(hours=1)) -> str:
        """Generate a JWT token for a user."""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str):
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Invalid signature — token tampered")
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Malformed token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token decode error: {str(e)}")

    # -------------------- OTP HANDLING --------------------
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP."""
        return str(random.randint(100000, 999999))

    @staticmethod
    async def send_otp_email(email: str, otp: str):
        """Send OTP to user email."""
        try:
            message = MIMEMultipart()
            message["From"] = settings.SMTP_USER
            message["To"] = email
            message["Subject"] = "Your OTP Code"
            message.attach(MIMEText(f"Your OTP is: {otp}", "plain"))

            if settings.SMTP_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)

            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
            server.quit()
            print(f"✅ OTP sent to {email}")

        except Exception as e:
            print(f"❌ Failed to send OTP: {e}")

    @staticmethod
    async def create_and_send_otp(email: str):
        """Create OTP, store it, and send via email."""
        otp = AuthService.generate_otp()
        await UserRepository.save_otp(email, otp)
        await AuthService.send_otp_email(email, otp)
        return otp

    @staticmethod
    async def verify_email_otp(email: str, otp: str) -> bool:
        """Verify user-provided OTP."""
        return await UserRepository.verify_otp(email, otp)

    @staticmethod
    async def is_email_verified(email: str) -> bool:
        """Check if email is verified."""
        return await UserRepository.is_email_verified(email)

    # -------------------- ADMIN LOGIN --------------------
    @staticmethod
    async def admin_login(email: str, password: str) -> dict:
        if email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD:
            payload = {
                "sub": email,
                "exp": datetime.utcnow() + timedelta(hours=12),
                "type": "admin"
            }
            access_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
            return {
                "email": email,
                "is_authenticated": True,
                "access_token": access_token,
                "token_type": "bearer",
                "message": "✅ Admin login successful"
            }
        return {
            "email": email,
            "is_authenticated": False,
            "message": "❌ Invalid admin credentials"
        }