import os

import requests
from loguru import logger


def post_message(message: str):
    """Posts message to a webhook."""
    webhook_url = os.getenv("DMDATA_WEBHOOK_URL", None)
    if not webhook_url:
        pass
    try:
        response = requests.post(webhook_url, data=message, timeout=5, headers={
            "Content-Type": "application/xml"
        })

        if response.status_code != 200:
            logger.warning(
                f"Failed to post DMData message to webhook: status_code={response.status_code}; content={response.text}"
            )
    except requests.exceptions.ConnectionError:
        logger.warning("Failed to post DMData message to webhook: request timeout.")
    except Exception:
        logger.exception("Failed to post DMData message to webhook.")
