import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


class Settings:
    PROJECT_NAME: str = "University API"

    # Lấy thông tin từ .env
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "123456")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "student_management")

    # Tạo DATABASE_URL động
    @property
    def DATABASE_URL(self) -> str:
        # URL encode the password to handle special characters
        encoded_password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{encoded_password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    raw_value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(raw_value) if raw_value and raw_value.strip() else 30

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "").strip()
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()
    SMTP_SENDER: str = os.getenv("SMTP_SENDER", SMTP_USERNAME)

    # Production defaults to https://learnbuild.dev; dev uses http://localhost:5173.
    # Override via FRONTEND_BASE_URL env variable.
    FRONTEND_BASE_URL: str = os.getenv("FRONTEND_BASE_URL", "https://learnbuild.dev")
    RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", 15))
    RATE_LIMIT_RESET_PER_HOUR: int = int(os.getenv("RATE_LIMIT_RESET_PER_HOUR", 5))
    

    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))


settings = Settings()
