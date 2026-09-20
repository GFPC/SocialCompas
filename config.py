import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "f9LHodD0cOKJ27213jylpqBMZA8H_P0u3QbcT1BLiTTddljfzGamPNuJ288lrt5pIhS9ho3Tkr0_PVCApNg8")
MAX_API_URL = os.getenv("MAX_API_URL", "https://platform-api2.max.ru").rstrip("/")
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() in ("true", "1", "t", "yes")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3307"))
MYSQL_USER = os.getenv("MYSQL_USER", "bot_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "bot_password")
MYSQL_DB = os.getenv("MYSQL_DB", "socialcompas_db")
