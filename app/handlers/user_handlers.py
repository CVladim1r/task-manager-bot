from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from models.models import User, Organization

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

    keyboard_first_start = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Список задач", callback_data="list_tasks"),
            InlineKeyboardButton(text="Создать задачу", callback_data="create_task")
        ],
        [
            InlineKeyboardButton(text="Создать организацию", callback_data="create_organization"),
            InlineKeyboardButton(text="Присоединиться к организации", callback_data="join_organization")
        ]
        # ,
        # [
        #     InlineKeyboardButton(text="Посмотреть все задачи", callback_data="view_all_tasks")
        # ]
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Список задач", callback_data="list_tasks"),
            InlineKeyboardButton(text="Создать задачу", callback_data="create_task")
        ],
        [
            InlineKeyboardButton(text="Задачи организации", callback_data="list_org_tasks_"),
        ],
        [
            InlineKeyboardButton(text="Создать задачу для организации", callback_data="create_org_tasks_")
        ]
    ])

    if created:
        await message.reply(f"Добро пожаловать, {user.first_name}! Вы можете создать организацию или продолжать использовать бота для личных задач.", reply_markup=keyboard_first_start)
    else:
        await message.reply(f"Рад видеть вас снова, {user.first_name}! Что хотите сделать дальше?", reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "create_organization")
async def process_create_organization(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название организации:")
    await state.set_state("waiting_for_org_name")
    await callback_query.answer()