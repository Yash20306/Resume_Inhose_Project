# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from fastapi import HTTPException
# import os
# import jwt

# from app.config.config import settings
# from app.services.auth.auth_service import AuthService
# from app.repository.user_repository import UserRepository
# from app.services.utils.log import logger


# class AuthAgentMiddleware(BaseHTTPMiddleware):
#     """
#     Secure middleware:
#     ✅ Verifies JWT tokens
#     ✅ Restricts access to /ai/* and /hr-admin/*
#     ✅ Ensures upload directories exist
#     """

#     async def dispatch(self, request: Request, call_next):
#         path = request.url.path.rstrip("/").lower()
#         logger.debug(f"Incoming Request Path: {path}")

#         # -------------------- PUBLIC ROUTES --------------------
#         public_exact_paths = {
#             "/api/v1/docs",
#             "/api/v1/openapi.json",
#             "/api/v1/redoc",
#             "/api/v1/favicon.ico",
#             "/favicon.ico",
#             "/",
#             "/api/v1/auth/admin/login",
#         }

#         public_suffixes = [
#             "register",
#             "login",
#             "verify-otp",
#             "resend-otp",
#             "admin/login",
#         ]

#         public_ai_suffixes = [
#             "ai/job/create",
#             # "ai/jobs/list",
#             "ai/resume/parse",
#             "ai/candidates/find",
#         ]

#         # ✅ Skip auth for public endpoints
#         if (
#             path in public_exact_paths
#             or any(path.endswith(suffix) for suffix in public_suffixes)
#             or any(path.endswith(suffix) for suffix in public_ai_suffixes)
#         ):
#             logger.debug(f"🟢 Public endpoint accessed: {path}")
#             return await call_next(request)

#         # -------------------- JWT AUTH CHECK --------------------
#         try:
#             auth_header = request.headers.get("Authorization")
#             if not auth_header or not auth_header.startswith("Bearer "):
#                 raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

#             token = auth_header[len("Bearer "):].strip()

#             # Decode token
#             try:
#                 payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
#             except jwt.ExpiredSignatureError:
#                 raise HTTPException(status_code=401, detail="Token expired")
#             except jwt.InvalidTokenError:
#                 raise HTTPException(status_code=401, detail="Malformed or invalid token")
            
#             logger.debug(f"payload is {payload}")
#             email = payload.get("sub")
#             token_type = payload.get("type", "user")

#             print(email)
#             print(token_type)

#             if not email:
#                 raise HTTPException(status_code=401, detail="Invalid token payload")

#             # -------------------- ADMIN AUTH --------------------
#             if email == settings.ADMIN_EMAIL or token_type == "admin":
#                 logger.debug(f"✅ Authenticated as Admin: {email}")

#                 # Allow Admin on everything
#                 if path.startswith("/api/v1/hr-admin/"):
#                     logger.debug("Admin accessing HR Dashboard routes")
#                 elif path.startswith("/api/v1/ai/"):
#                     logger.debug("Admin accessing AI routes")

#                 request.state.user = {"email": email, "role": "admin"}
#                 await self.ensure_upload_folders()
#                 return await call_next(request)

#             # -------------------- NORMAL USER AUTH --------------------
#             user = None
#             if token_type == "user":
#                 try:
#                     logger.debug("inside user search")
#                     logger.debug(f"email is {email}")
#                     user = await UserRepository.find_by_email(email)
#                 except Exception as e:
#                     logger.error(f"User lookup failed: {str(e)}")

#                 logger.debug(f"user found! is {user}")

#                 # if not user:
#                 #     logger.debug("user not found!")
#                 #     raise HTTPException(status_code=401, detail="User not found")

#                 if not user.get("is_email_verified", False):
#                     raise HTTPException(status_code=403, detail="Email not verified")

#             # -------------------- AI ACCESS --------------------
#             if path.startswith("/api/v1/ai/"):
#                 if not settings.GEMINI_API_KEY:
#                     logger.error("Gemini API key missing in environment.")
#                     raise HTTPException(status_code=500, detail="AI configuration missing")

#                 await self.ensure_upload_folders()
#                 logger.debug(f"✅ Verified user accessing AI routes: {email}")

#             # -------------------- HR ADMIN ACCESS CONTROL --------------------
#             if path.startswith("/api/v1/hr-admin/"):
#                 raise HTTPException(status_code=403, detail="Only admin can access HR dashboard")

#             request.state.user = user
#             logger.debug(f"{user}")
#             await self.ensure_upload_folders()
#             return await call_next(request)

#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"❌ Middleware error: {str(e)}")
#             raise HTTPException(status_code=500, detail="Internal server error")
#     # -------------------- HELPER: Ensure Upload Folders --------------------
#     @staticmethod
#     async def ensure_upload_folders():
#         """
#         Creates required upload directories if missing.
#         """
#         upload_dirs = [
#             "uploads",
#             os.path.join("uploads", "requirements"),
#             os.path.join("uploads", "resumes"),
#             os.path.join("uploads", "match_results"),
#         ]
#         for folder in upload_dirs:
#             os.makedirs(folder, exist_ok=True)
#             logger.debug(f"Ensured upload folder exists: {folder}")



from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException
import os
import jwt

from app.config.config import settings
from app.services.auth.auth_service import AuthService
from app.repository.user_repository import UserRepository
from app.services.utils.log import logger


class AuthAgentMiddleware(BaseHTTPMiddleware):
    """
    Secure middleware:
    ✅ Verifies JWT tokens
    ✅ Restricts access to /ai/* and /hr-admin/*
    ✅ Ensures upload directories exist
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/").lower()
        logger.debug(f"Incoming Request Path: {path}")

        # ✅ Allow CORS preflight requests
        if request.method == "OPTIONS":
            logger.debug("🟢 Preflight OPTIONS request — skipping auth")
            return await call_next(request)

        # -------------------- PUBLIC ROUTES --------------------
        public_exact_paths = {
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/redoc",
            "/api/v1/favicon.ico",
            "/favicon.ico",
            "/",
            "/api/v1/auth/admin/login",
        }

        public_suffixes = [
            "register",
            "login",
            "verify-otp",
            "resend-otp",
            "admin/login",
        ]

        public_ai_suffixes = [
            "ai/job/create",
            "ai/resume/parse",
            "ai/candidates/find",
        ]

        # ✅ Skip auth for public endpoints
        if (
            path in public_exact_paths
            or any(path.endswith(suffix) for suffix in public_suffixes)
            or any(path.endswith(suffix) for suffix in public_ai_suffixes)
        ):
            logger.debug(f"🟢 Public endpoint accessed: {path}")
            return await call_next(request)

        # -------------------- JWT AUTH CHECK --------------------
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

            token = auth_header[len("Bearer "):].strip()

            # Decode token
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Malformed or invalid token")
            
            logger.debug(f"payload is {payload}")
            email = payload.get("sub")
            token_type = payload.get("type", "user")

            if not email:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # -------------------- ADMIN AUTH --------------------
            if email == settings.ADMIN_EMAIL or token_type == "admin":
                logger.debug(f"✅ Authenticated as Admin: {email}")

                # Allow Admin on everything
                if path.startswith("/api/v1/hr-admin/"):
                    logger.debug("Admin accessing HR Dashboard routes")
                elif path.startswith("/api/v1/ai/"):
                    logger.debug("Admin accessing AI routes")

                request.state.user = {"email": email, "role": "admin"}
                await self.ensure_upload_folders()
                return await call_next(request)

            # -------------------- NORMAL USER AUTH --------------------
            user = None
            if token_type == "user":
                try:
                    logger.debug("inside user search")
                    logger.debug(f"email is {email}")
                    user = await UserRepository.find_by_email(email)
                except Exception as e:
                    logger.error(f"User lookup failed: {str(e)}")

                logger.debug(f"user found! is {user}")

                if not user.get("is_email_verified", False):
                    raise HTTPException(status_code=403, detail="Email not verified")

            # -------------------- AI ACCESS --------------------
            if path.startswith("/api/v1/ai/"):
                if not settings.GEMINI_API_KEY:
                    logger.error("Gemini API key missing in environment.")
                    raise HTTPException(status_code=500, detail="AI configuration missing")

                await self.ensure_upload_folders()
                logger.debug(f"✅ Verified user accessing AI routes: {email}")

            # -------------------- HR ADMIN ACCESS CONTROL --------------------
            if path.startswith("/api/v1/hr-admin/"):
                raise HTTPException(status_code=403, detail="Only admin can access HR dashboard")

            request.state.user = user
            logger.debug(f"{user}")
            await self.ensure_upload_folders()
            return await call_next(request)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Middleware error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    # -------------------- HELPER: Ensure Upload Folders --------------------
    @staticmethod
    async def ensure_upload_folders():
        """
        Creates required upload directories if missing.
        """
        upload_dirs = [
            "uploads",
            os.path.join("uploads", "requirements"),
            os.path.join("uploads", "resumes"),
            os.path.join("uploads", "match_results"),
        ]
        for folder in upload_dirs:
            os.makedirs(folder, exist_ok=True)
            logger.debug(f"Ensured upload folder exists: {folder}")
