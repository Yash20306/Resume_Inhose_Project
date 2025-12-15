import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import smtplib

load_dotenv()  


class Settings:
    # -------------------- DATABASE CONFIG --------------------
    MONGO_URI: str = os.getenv("MONGO_URI")
    DB_NAME: str = os.getenv("DB_NAME", "DB_name")

    # -------------------- AUTH CONFIG --------------------
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    JWT_ALGORITHM: str = "HS256"

    # -------------------- GEMINI CONFIG --------------------
    GEMINI_API_KEY: str = os.getenv(
        "GEMINI_API_KEY",
        "Your-api-key"
    )

    llm: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=GEMINI_API_KEY,
    )

    # -------------------- EMAIL CONFIG --------------------
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "your_gmail")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "your_app_password")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() in ("true", "1")

    # -------------------- APOLLO.IO CONFIG --------------------
    APOLLO_API_KEY: str = os.getenv(
        "APOLLO_API_KEY",
        "Your-key"
    )

    # -------------------- FOLDER CONFIG --------------------
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    REQUIREMENT_FOLDER: str = os.path.join(UPLOAD_FOLDER, "requirements")
    RESUME_FOLDER: str = os.path.join(UPLOAD_FOLDER, "resumes")
    MATCH_RESULT: str = os.path.join(UPLOAD_FOLDER,"match_results")

    # Create folders safely
    for folder in [UPLOAD_FOLDER, REQUIREMENT_FOLDER, RESUME_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # -------------------- ADMIN CONFIG --------------------
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@123")

    FRONTEND_URL: str = "http://localhost:5173"  # 👈 change if frontend runs elsewhere



# Global instance
settings = Settings()
