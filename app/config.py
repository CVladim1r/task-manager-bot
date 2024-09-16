import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "None")
DB_URL = os.getenv("DATABASE_URL")

db_user = "root"
db_pass = "q1q1q1q1"
db_port = "3306"
db_host = "localhost"
db_name = "taskmanager"
db_url = f"mysql://root:q1q1q1q1@localhost:3306/taskmanager"

TORTOISE_ORM = {
    "connections": {
        "default": db_url,
    },
    "apps": {
        "models": {
            "models": ["task_manager.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}
