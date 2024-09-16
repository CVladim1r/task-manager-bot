from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from models.models import User, Organization

router = Router()

@router.message(Command("create_organization"))
async def create_organization(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("Использование: /create_organization <название> <описание>")
        return
    
    name = args[1]
    description = args[2]

    user = await User.get(telegram_id=message.from_user.id)
    organization = await Organization.create(name=name, description=description, created_by=user)

    await message.reply(f"Организация {name} создана!")
