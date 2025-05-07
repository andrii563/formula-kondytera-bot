import logging
import sys
from datetime import datetime
from logging import StreamHandler


class Colors:
    HEADER = "\033[95m"
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    CRITICAL = "\033[41m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DEBUG = "\033[37m"


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        orig_levelname = record.levelname

        if record.levelno == logging.DEBUG:
            record.levelname = f"{Colors.DEBUG}{orig_levelname}{Colors.RESET}"
        elif record.levelno == logging.INFO:
            record.levelname = f"{Colors.INFO}{orig_levelname}{Colors.RESET}"
        elif record.levelno == logging.WARNING:
            record.levelname = f"{Colors.WARNING}{orig_levelname}{Colors.RESET}"
        elif record.levelno == logging.ERROR:
            record.levelname = f"{Colors.ERROR}{orig_levelname}{Colors.RESET}"
        elif record.levelno == logging.CRITICAL:
            record.levelname = (
                f"{Colors.CRITICAL}{Colors.BOLD}{orig_levelname}{Colors.RESET}"
            )

        dt_fmt = "%H:%M:%S %d-%m-%Y"
        record.asctime = datetime.now().strftime(dt_fmt)

        log_line = f"{record.asctime} | {record.levelname}: {record.msg}"
        total_length = 100
        spaces_needed = total_length - len(log_line)
        return f"{log_line}{' ' * spaces_needed}"


def setup_logging():
    logger = logging.getLogger("formula-kondytera-bot")
    logger.setLevel(logging.DEBUG)

    console_handler = StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter(
        fmt="%(message)s",
        datefmt="%H:%M:%S %d-%m-%Y",
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()
