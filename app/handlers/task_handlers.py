from aiogram import types, Router
from aiogram.filters import Command
from models.models import User, Task
from aiogram.fsm.storage.memory import MemoryStorage
from tortoise.exceptions import DoesNotExist
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from models.models import User, Task

router = Router()

class TaskCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_reminder_time = State()

@router.callback_query(lambda c: c.data == "create_task")
async def process_create_task(callback_query: types.CallbackQuery, state: FSMContext):
    await create_task_start(callback_query.message, state)

@router.message(Command("create_task"))
async def create_task_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название задачи:")
    await state.set_state(TaskCreation.waiting_for_name)

@router.message(TaskCreation.waiting_for_name)
async def process_task_name(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("Введите описание задачи:")
    await state.set_state(TaskCreation.waiting_for_description)

@router.message(TaskCreation.waiting_for_description)
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(task_description=message.text)
    await message.answer("Введите дедлайн задачи (в формате YYYY-MM-DD HH:MM):")
    await state.set_state(TaskCreation.waiting_for_deadline)

@router.message(TaskCreation.waiting_for_deadline)
async def process_task_deadline(message: types.Message, state: FSMContext):
    await state.update_data(task_deadline=message.text)
    await message.answer("Введите время напоминания (в формате YYYY-MM-DD HH:MM):")
    await state.set_state(TaskCreation.waiting_for_reminder_time)

@router.message(TaskCreation.waiting_for_reminder_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
    await state.update_data(task_reminder_time=message.text)
    user_data = await state.get_data()

    user = await User.get(telegram_id=message.from_user.id)

    task = await Task.create(
        name=user_data['task_name'],
        description=user_data['task_description'],
        deadline=user_data['task_deadline'],
        reminder_time=user_data['task_reminder_time'],
        created_by=user
    )

    await message.answer(f"Задача '{user_data['task_name']}' успешно создана!")
    
    await state.clear()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.message(Command("list_tasks"))
async def list_tasks(message: types.Message):
    user = await User.get(telegram_id=message.from_user.id)
    tasks = await Task.filter(created_by=user).all()

    if not tasks:
        await message.reply("У вас нет задач.")
        return

    for task in tasks:
        deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M")
        reminder_time_str = task.reminder_time.strftime("%Y-%m-%d %H:%M")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Редактировать", callback_data=f"edit_task_{task.id}"),
                InlineKeyboardButton(text="Выполнена", callback_data=f"complete_task_{task.id}")
            ]
        ])

        await message.answer(
            f"Задача: {task.name}\n"
            f"Дедлайн: {deadline_str}\n"
            f"Напоминание: {reminder_time_str}",
            reply_markup=keyboard
        )


@router.message(Command("assign_task"))
async def assign_task(message: types.Message):
    args = message.text.split(maxsplit=3)
    if len(args) < 3:
        await message.reply("Использование: /assign_task <task_id> <user_id>")
        return

    task_id = int(args[1])
    user_id = int(args[2])

    try:
        task = await Task.get(id=task_id)
        user = await User.get(id=user_id)
        await task.assigned_users.add(user)

        await message.reply(f"Задача '{task.name}' назначена пользователю {user.first_name} {user.last_name}.")
    except DoesNotExist:
        await message.reply("Задача или пользователь не найдены.")


from aiogram import types
from aiogram.types import CallbackQuery

@router.callback_query(lambda c: c.data == "list_tasks")
async def process_list_tasks(callback_query: CallbackQuery):
    user = await User.get(telegram_id=callback_query.from_user.id)
    tasks = await Task.filter(created_by=user).all()

    if not tasks:
        await callback_query.message.reply("У вас нет задач.")
        return

    for task in tasks:
        deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M")
        reminder_time_str = task.reminder_time.strftime("%Y-%m-%d %H:%M")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Редактировать", callback_data=f"edit_task_{task.id}"),
                InlineKeyboardButton(text="Выполнена", callback_data=f"complete_task_{task.id}")
            ]
        ])

        await callback_query.message.answer(
            f"Задача: {task.name}\n"
            f"Дедлайн: {deadline_str}\n"
            f"Напоминание: {reminder_time_str}",
            reply_markup=keyboard
        )


@router.callback_query(lambda c: c.data == "create_organization")
async def process_create_organization(callback_query: CallbackQuery):
    await callback_query.message.edit_text("Введите название и описание организации с помощью команды /create_organization")


@router.callback_query(lambda c: c.data == "go_back")
async def process_go_back(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Список задач", callback_data="list_tasks"),
            InlineKeyboardButton(text="Создать задачу", callback_data="create_task")
        ]
    ])
    
    await callback_query.message.edit_text("Выберите действие:", reply_markup=keyboard)


from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from models.models import Task

@router.callback_query(F.text(startswith="edit_task_"))
async def edit_task(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split("_")[2])
    task = await Task.get(id=task_id)
    
    await callback_query.message.answer(f"Введите новое название для задачи '{task.name}':")
    await callback_query.answer()  # Подтверждение нажатия на кнопку

    await state.update_data(task_id=task_id)
    await state.set_state(TaskCreation.waiting_for_name)

@router.callback_query(lambda c: c.data == "complete_task_")
async def complete_task(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split("_")[2])
    task = await Task.get(id=task_id)
    
    task.completed = True
    await task.save()
    
    await callback_query.message.answer(f"Задача '{task.name}' отмечена как выполненная.")
    await callback_query.answer()  # Подтверждение нажатия на кнопку

    
@router.message(TaskCreation.waiting_for_name)
async def process_task_name(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("Введите описание задачи:")
    await state.set_state(TaskCreation.waiting_for_description)
