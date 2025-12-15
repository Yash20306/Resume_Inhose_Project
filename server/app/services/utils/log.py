import logging
from datetime import datetime

import pytz

IST = pytz.timezone("Asia/Kolkata")


class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=IST)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


logger = logging.getLogger("Master")
logger.setLevel(logging.DEBUG)

logger.propagate = False
logger.handlers.clear()

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = ISTFormatter(
    "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(handler)
