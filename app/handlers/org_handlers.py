from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from tortoise.exceptions import DoesNotExist

from models.models import User, Organization, Task
import random
import string
import logging

logger = logging.getLogger(__name__)

router = Router()

class OrganizationStates(StatesGroup):
    waiting_for_org_name = State()
    waiting_for_org_description = State()
    waiting_for_org_code = State()
    
class TaskStates(StatesGroup):
    waiting_for_org_task_name = State()
    waiting_for_org_task_description = State()
    waiting_for_org_task_deadline = State()
    waiting_for_org_task_reminder_time = State()

class EditTaskStates(StatesGroup):
    waiting_for_task_id = State()
    waiting_for_new_task_name = State()
    waiting_for_new_task_description = State()
    waiting_for_new_task_deadline = State()
    waiting_for_new_task_reminder_time = State()

@router.message(Command("create_organization"))
async def create_organization(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated organization creation.")
    await message.answer("Введите название организации:")
    await state.set_state(OrganizationStates.waiting_for_org_name)

@router.message(OrganizationStates.waiting_for_org_name)
async def process_org_name(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} provided organization name: {message.text}")
    await state.update_data(org_name=message.text)
    await message.answer("Введите описание организации:")
    await state.set_state(OrganizationStates.waiting_for_org_description)

@router.message(OrganizationStates.waiting_for_org_description)
async def process_org_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    org_name = data['org_name']
    org_description = message.text

    user = await User.get(telegram_id=message.from_user.id)
    special_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    organization = await Organization.create(
        name=org_name,
        description=org_description,
        created_by=user,
        code=special_code
    )

    await user.organizations.add(organization)
    logger.info(f"Organization '{org_name}' created by user {user.telegram_id} with code {special_code}.")
    await message.answer(f"Организация '{org_name}' создана. Код для присоединения: {special_code}.")
    await state.clear()

@router.message(Command("join_organization"))
async def join_organization(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated joining an organization.")
    await message.answer("Введите код организации для присоединения:")
    await state.set_state(OrganizationStates.waiting_for_org_code)

@router.message(OrganizationStates.waiting_for_org_code)
async def process_org_code(message: types.Message, state: FSMContext):
    code = message.text
    try:
        organization = await Organization.get(code=code)
        user = await User.get(telegram_id=message.from_user.id)

        await organization.members.add(user)
        logger.info(f"User {user.telegram_id} joined organization '{organization.name}'.")
        await message.answer(f"Вы присоединились к организации '{organization.name}'.")
    except DoesNotExist:
        logger.warning(f"User {message.from_user.id} attempted to join organization with invalid code: {code}.")
        await message.reply("Неверный код. Попробуйте снова.")

@router.message(Command("create_org_task"))
async def create_task_start(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated task creation.")
    await message.answer("Введите название задачи:")
    await state.set_state(TaskStates.waiting_for_org_task_name)

@router.callback_query(lambda c: c.data.startswith("create_org_tasks_"))
async def create_org_task_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название задачи для организации:")
    await state.set_state(TaskStates.waiting_for_org_task_name)

@router.message(TaskStates.waiting_for_org_task_name)
async def process_task_name(message: types.Message, state: FSMContext):
    await state.update_data(task_name=message.text)
    await message.answer("Введите описание задачи:")
    await state.set_state(TaskStates.waiting_for_org_task_description)

@router.message(TaskStates.waiting_for_org_task_description)
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(task_description=message.text)
    await message.answer("Введите дедлайн задачи (в формате YYYY-MM-DD HH:MM):")
    await state.set_state(TaskStates.waiting_for_org_task_deadline)

@router.message(TaskStates.waiting_for_org_task_deadline)
async def process_task_deadline(message: types.Message, state: FSMContext):
    await state.update_data(task_deadline=message.text)
    await message.answer("Введите время напоминания (в формате YYYY-MM-DD HH:MM):")
    await state.set_state(TaskStates.waiting_for_org_task_reminder_time)

@router.message(TaskStates.waiting_for_org_task_reminder_time)
async def process_reminder_time(message: types.Message, state: FSMContext):
    await state.update_data(task_reminder_time=message.text)
    
    user_data = await state.get_data()
    user = await User.get(telegram_id=message.from_user.id)

    organization = await Organization.get(members=user)

    await Task.create(
        name=user_data['task_name'],
        description=user_data['task_description'],
        deadline=user_data['task_deadline'],
        reminder_time=user_data['task_reminder_time'],
        created_by=user,
        organization=organization,
        status="pending"
    )

    logger.info(f"Task '{user_data['task_name']}' created in organization '{organization.name}' by user {user.telegram_id}.")
    await message.answer(f"Задача '{user_data['task_name']}' успешно создана!")
    await state.clear()

@router.message(Command("list_org_tasks"))
async def list_tasks(message: types.Message):
    user = await User.get(telegram_id=message.from_user.id)
    organizations = await user.organizations.all()

    if not organizations:
        await message.reply("У вас нет организации.")
        return
    
    tasks_message = "Задачи организации:\n"
    await message.answer(tasks_message)

    for organization in organizations:

        tasks = await organization.tasks.all()
        for task in tasks:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=f"Редактировать задачу {task.id}", callback_data=f"edit_task_{task.id}"),
                    InlineKeyboardButton(text="Сделать выполненной", callback_data=f"complete_task_{task.id}")
                ]
            ])

            await message.answer(
                f"ID задачи: {task.id}\n"
                f"Задача: {task.name}\n"
                f"Статус: {task.status}\n"
                f"Дедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n\n",
                reply_markup=keyboard
            )
        


@router.callback_query(lambda c: c.data.startswith("list_org_tasks_"))
async def list_org_tasks(callback_query: types.CallbackQuery):
    user = await User.get(telegram_id=callback_query.from_user.id)
    organizations = await user.organizations.all()

    if not organizations:
        await callback_query.message.reply("У вас нет организации.")
        return
    
    tasks_message = "Задачи организации:\n"

    for organization in organizations:

        tasks = await organization.tasks.all()
        for task in tasks:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=f"Редактировать задачу {task.id}", callback_data=f"edit_task_{task.id}"),
                    InlineKeyboardButton(text="Сделать выполненной", callback_data=f"complete_task_{task.id}")
                ]
            ])

            await callback_query.message.answer(
                f"ID задачи: {task.id}\n"
                f"Задача: {task.name}\n"
                f"Статус: {task.status}\n"
                f"Дедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}\n\n",
                reply_markup=keyboard
            )
        
        await callback_query.message.answer(tasks_message)

    await callback_query.answer()



@router.message(Command("edit_org_task"))
async def edit_task_start(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated task editing.")
    await message.answer("Введите ID задачи для редактирования:")
    await state.set_state(EditTaskStates.waiting_for_task_id)

@router.message(EditTaskStates.waiting_for_task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    task_id = message.text
    try:
        task = await Task.get(id=task_id)
        await state.update_data(task=task)\
        
        await message.answer(f"Вы выбрали задачу: '{task.name}'.\nВведите новое название задачи (или нажмите 'Пропустить' для сохранения текущего):")
        await state.set_state(EditTaskStates.waiting_for_new_task_name)
    except DoesNotExist:
        logger.warning(f"User {message.from_user.id} attempted to edit a non-existent task with ID: {task_id}.")
        await message.reply("Задача с таким ID не найдена. Попробуйте снова.")

@router.message(EditTaskStates.waiting_for_new_task_name)
async def process_new_task_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task = data['task']
    
    new_name = message.text if message.text.strip() else task.name
    task.name = new_name
    await task.save()
    
    await message.answer("Введите новое описание задачи (или нажмите 'Пропустить' для сохранения текущего):")
    await state.set_state(EditTaskStates.waiting_for_new_task_description)

@router.message(EditTaskStates.waiting_for_new_task_description)
async def process_new_task_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task = data['task']
    
    new_description = message.text if message.text.strip() else task.description  # Keep current description if input is empty
    task.description = new_description
    await task.save()
    
    await message.answer("Введите новый дедлайн задачи (в формате YYYY-MM-DD HH:MM, или нажмите 'Пропустить' для сохранения текущего):")
    await state.set_state(EditTaskStates.waiting_for_new_task_deadline)

@router.message(EditTaskStates.waiting_for_new_task_deadline)
async def process_new_task_deadline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task = data['task']
    
    new_deadline = message.text if message.text.strip() else task.deadline.strftime('%Y-%m-%d %H:%M')  # Keep current deadline if input is empty
    task.deadline = new_deadline
    await task.save()
    
    await message.answer("Введите новое время напоминания (в формате YYYY-MM-DD HH:MM, или нажмите 'Пропустить' для сохранения текущего):")
    await state.set_state(EditTaskStates.waiting_for_new_task_reminder_time)

@router.message(EditTaskStates.waiting_for_new_task_reminder_time)
async def process_new_task_reminder_time(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task = data['task']
    
    new_reminder_time = message.text if message.text.strip() else task.reminder_time.strftime('%Y-%m-%d %H:%M')  # Keep current reminder if input is empty
    task.reminder_time = new_reminder_time
    await task.save()
    
    logger.info(f"Task '{task.name}' updated successfully by user {message.from_user.id}.")
    await message.answer(f"Задача '{task.name}' успешно обновлена!")
    await state.clear()
