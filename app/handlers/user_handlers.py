from aiogram import types, Router
from aiogram.filters import Command
from models.models import User
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):
    user, created = await User.get_or_create(
        telegram_id=message.from_user.id,
        defaults={
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name
        }
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Список задач", callback_data="list_tasks"),
            InlineKeyboardButton(text="Создать задачу", callback_data="create_task")
        ],
        [
            InlineKeyboardButton(text="Создать организацию", callback_data="create_organization")
        ]
    ])

    if created:
        await message.reply(f"Добро пожаловать, {user.first_name}! Вы успешно зарегистрированы.", reply_markup=keyboard)
    else:
        await message.reply(f"Рад видеть вас снова, {user.first_name}!", reply_markup=keyboard)
