from datetime import datetime
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tortoise.exceptions import DoesNotExist

from models.models import User, Task, Organization

router = Router()

class TaskCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_deadline = State()
    waiting_for_reminder_time = State()

def validate_datetime(input_string: str) -> bool:
    try:
        datetime.strptime(input_string, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

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
    if validate_datetime(message.text):
        await state.update_data(task_deadline=message.text)
        await message.answer("Введите время напоминания (в формате YYYY-MM-DD HH:MM):")
        await state.set_state(TaskCreation.waiting_for_reminder_time)
    else:
        await message.answer("Неправильный формат даты. Пожалуйста, попробуйте снова (в формате YYYY-MM-DD HH:MM):")

@router.message(TaskCreation.waiting_for_reminder_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
    if validate_datetime(message.text):
        await state.update_data(task_reminder_time=message.text)
        user_data = await state.get_data()
        user = await User.get(telegram_id=message.from_user.id)

        await Task.create(
            name=user_data['task_name'],
            description=user_data['task_description'],
            deadline=user_data['task_deadline'],
            reminder_time=user_data['task_reminder_time'],
            created_by=user,
            status="pending"
        )

        await message.answer(f"Задача '{user_data['task_name']}' успешно создана!")    
        await state.clear()
    else:
        await message.answer("Неправильный формат времени. Пожалуйста, попробуйте снова (в формате YYYY-MM-DD HH:MM):")

@router.callback_query(lambda c: c.data.startswith("list_tasks"))
async def list_tasks_callback_query(callback_query: types.CallbackQuery):
    user = await User.get(telegram_id=callback_query.from_user.id)
    tasks = await Task.filter(created_by=user).all()

    if not tasks:
        await callback_query.message.reply("У вас нет задач.")
        return

    for task in tasks:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Редактировать", callback_data=f"edit_task_{task.id}"),
                InlineKeyboardButton(text="Сделать выполненной", callback_data=f"complete_task_{task.id}")
            ]
        ])

        await callback_query.message.answer(
            f"Задача: {task.name}\n"
            f"Статус: {task.status}\n"
            f"Дедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n"
            f"Напоминание: {task.reminder_time.strftime('%Y-%m-%d %H:%M')}",
            reply_markup=keyboard
        )

@router.message(Command("list_tasks"))
async def list_tasks(message: types.Message):
    user = await User.get(telegram_id=message.from_user.id)
    tasks = await Task.filter(created_by=user).all()

    if not tasks:
        await message.reply("У вас нет задач.")
        return

    for task in tasks:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Редактировать", callback_data=f"edit_task_{task.id}"),
                InlineKeyboardButton(text="Сделать выполненной", callback_data=f"complete_task_{task.id}")
            ]
        ])

        await message.answer(
            f"Задача: {task.name}\n"
            f"Статус: {task.status}\n"
            f"Дедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n"
            f"Напоминание: {task.reminder_time.strftime('%Y-%m-%d %H:%M')}",
            reply_markup=keyboard
        )

@router.callback_query(lambda c: c.data.startswith("complete_task_"))
async def complete_task(callback_query: types.CallbackQuery):
    task_id = callback_query.data.split("_")[2]
    try:
        task = await Task.get(id=task_id)
        await task.delete()

        await callback_query.answer("Задача успешно сделана выполненной!")
        await callback_query.message.edit_text(f"Задача '{task.name}' была сделана выполненной и удалена.")
    except DoesNotExist:
        await callback_query.answer("Задача не найдена.")
import logging

@router.callback_query(lambda c: c.data.startswith("edit_task_"))
async def edit_task(callback_query: types.CallbackQuery, state: FSMContext):
    logging.info("Edit task callback received")

    task_id = int(callback_query.data.split("_")[2])
    
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        await callback_query.answer("Задача не найдена.")
        return

    await callback_query.message.answer(f"Введите новое название для задачи '{task.name}':")
    await callback_query.answer()

    await state.update_data(task_id=task_id)
    await state.set_state(TaskCreation.waiting_for_name)

@router.message(TaskCreation.waiting_for_name)
async def process_task_name(message: types.Message, state: FSMContext):
    task_id = (await state.get_data())['task_id']
    
    try:
        task = await Task.get(id=task_id)
    except DoesNotExist:
        await message.answer("Задача не найдена, пожалуйста, попробуйте снова.")
        await state.clear()
        return

    task.name = message.text
    await task.save()
    
    await message.answer("Название задачи обновлено. Введите новое описание:")
    await state.set_state(TaskCreation.waiting_for_description)


@router.message(TaskCreation.waiting_for_description)
async def process_task_description(message: types.Message, state: FSMContext):
    task_id = (await state.get_data())['task_id']
    task = await Task.get(id=task_id)

    task.description = message.text
    await task.save()
    
    await message.answer("Описание задачи обновлено. Введите новый дедлайн (в формате YYYY-MM-DD HH:MM):")
    await state.set_state(TaskCreation.waiting_for_deadline)

@router.message(TaskCreation.waiting_for_deadline)
async def process_task_deadline(message: types.Message, state: FSMContext):
    task_id = (await state.get_data())['task_id']
    task = await Task.get(id=task_id)

    if validate_datetime(message.text):
        task.deadline = message.text
        await task.save()
        
        await message.answer("Дедлайн задачи обновлен. Введите новое время напоминания (в формате YYYY-MM-DD HH:MM):")
        await state.set_state(TaskCreation.waiting_for_reminder_time)
    else:
        await message.answer("Неправильный формат даты. Пожалуйста, попробуйте снова (в формате YYYY-MM-DD HH:MM):")

@router.message(TaskCreation.waiting_for_reminder_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
    task_id = (await state.get_data())['task_id']
    task = await Task.get(id=task_id)

    if validate_datetime(message.text):
        task.reminder_time = message.text
        await task.save()
        
        await message.answer(f"Задача '{task.name}' успешно обновлена!")
        await state.clear()
    else:
        await message.answer("Неправильный формат времени. Пожалуйста, попробуйте снова (в формате YYYY-MM-DD HH:MM):")
