"""
Centralized configuration for the NartBooks API.
Environment variables can override default values when necessary.
"""

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nartbooks.db")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "my_secret_token")

MSG_OVRX_BASE_URL = os.getenv("MSG_OVRX_BASE_URL", "https://msg.ovrx.ru")
MSG_OVRX_API_KEY = os.getenv("MSG_OVRX_API_KEY", "ТВОЙ_API_КЛЮЧ")

