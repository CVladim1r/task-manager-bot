import asyncio
from aiogram import Bot
from models.models import Task
from datetime import datetime, timezone

async def send_reminders(bot: Bot):
    while True:
        current_time = datetime.now(timezone.utc)
        tasks = await Task.filter(reminder_time__lte=current_time, reminder_sent=False).all()

        for task in tasks:
            await task.fetch_related('created_by')
            user = task.created_by
            
            if user and user.telegram_id:
                time_left = task.deadline - current_time
                
                days, seconds = divmod(time_left.total_seconds(), 86400)
                hours, seconds = divmod(seconds, 3600)
                minutes = seconds // 60
                
                deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M")
                reminder_time_str = task.reminder_time.strftime("%Y-%m-%d %H:%M")
        

                time_parts = []
                if days > 0:
                    time_parts.append(f"{int(days)} дн.")
                if hours > 0:
                    time_parts.append(f"{int(hours)} ч.")
                if minutes > 0:
                    time_parts.append(f"{int(minutes)} мин.")

                time_left_str = ", ".join(time_parts) if time_parts else "меньше минуты"

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"Напоминание! Задача '{task.name}' скоро истекает. Дедлайн: {deadline_str}. "
                        f"Осталось времени: {time_left_str}."
                )

                task.reminder_sent = True
                await task.save()

        await asyncio.sleep(60)
