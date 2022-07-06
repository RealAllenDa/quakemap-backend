__all__ = ["BaseModule"]

from sdk import todo


class BaseModule:
    """
    Foundation for all the modules/api fetchers.
    """

    def __init__(self):
        self.info = None

    def get_info(self) -> None:
        """
        API's main entry point.
        """
        todo()
