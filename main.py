import os
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from dotenv import load_dotenv
import asyncio

load_dotenv()

from aiogram.fsm.storage.memory import MemoryStorage
from app.handlers.task_handlers import router as task_router
from app.handlers.org_handlers import router as org_router
from app.handlers.user_handlers import router as user_router

from utils.reminders import send_reminders

TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

app = FastAPI()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

dp.include_router(task_router)
dp.include_router(org_router)
dp.include_router(user_router)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запуск бота"),
        BotCommand(command="/create_task", description="Создать задачу"),
        BotCommand(command="/list_tasks", description="Список задач"),
        BotCommand(command="/assign_task", description="Назначить задачу"),
        BotCommand(command="/create_organization", description="Создать организацию"),
    ]
    await bot.set_my_commands(commands)

async def start_bot():
    await dp.start_polling(bot)


@app.on_event("startup")
async def on_startup():
    register_tortoise(
        app,
        db_url=DB_URL,
        modules={"models": ["models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
    asyncio.create_task(set_bot_commands(bot))
    asyncio.create_task(send_reminders(bot))
    asyncio.create_task(start_bot())

@app.get("/")
async def root():
    return {"message": "FastAPI and Telegram bot are running!"}
