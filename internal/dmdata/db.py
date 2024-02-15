import asyncio
import platform

from loguru import logger

from models import DbMessages
from schemas.dmdata.socket import DmdataSocketData


def store_message_middleware(*params):
    if platform.system() == 'Windows':
        # prevent extremely rare cases where there are too many event loops,
        # preventing new loops from creating.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(store_message(*params))


async def store_message(message: DmdataSocketData, xml_message: dict):
    """Stores data message to the database."""
    base = message.xmlReport
    if base is None:
        logger.error("Failed to store data message to the database: no xmlReport available")
        return
    logger.debug(
        f"Storing message to the database -> {base.head.event_id} / {base.head.serial} at {base.head.report_date}"
    )
    from env import Env
    if base.head.serial is None:
        serial = 0
    else:
        serial = int(base.head.serial)

    session = None
    try:
        session = await Env.db_instance.get_session()
        message = DbMessages(
            type=message.head.type.value,
            event_id=base.head.event_id,
            serial=serial,
            event_time=base.head.target_date,
            data=xml_message
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
    except Exception:
        logger.exception("Failed to store message to the database.")
    finally:
        if session:
            await session.invalidate()
