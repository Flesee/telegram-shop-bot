from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.mailing_service import process_mailings


def setup_scheduler(bot) -> AsyncIOScheduler:
    """Настройка планировщика задач"""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        process_mailings,
        'interval',
        seconds=20,
        args=[bot]
    )
    
    return scheduler
