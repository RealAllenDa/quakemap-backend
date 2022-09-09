import os
import sys

from loguru import logger

from env import Env


class DMDataFetcher:
    """
    Fetches DMData.
    """

    def __init__(self):
        self.client_id = Env.config.dmdata.client_id
        self.client_token = Env.config.dmdata.client_token
        if self.client_id == "" or self.client_token == "":
            logger.critical("Failed to initialize DMData: No client_id or client_token specified.")
            sys.exit(1)

        self.refresh_token = os.getenv("REFRESH_TOKEN")
        if self.refresh_token is None:
            logger.critical("Failed to initialize DMData: No REFRESH_TOKEN defined in environ.")
            sys.exit(1)
