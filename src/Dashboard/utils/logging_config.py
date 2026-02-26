import logging
import sys
from logging.handlers import RotatingFileHandler
import colorlog


def setup_logging(
    level: str = "DEBUG",
    log_file: str = "app.log",
    max_bytes: int = 5_000_000,
    backup_count: int = 3,
):
    """
    Configure root logging with:
    - Colored console output
    - Rotating file handler
    """

    numeric_level = getattr(logging, level.upper(), logging.DEBUG)

    root_logger = logging.getLogger()

    # 🔥 Limpiar handlers previos
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(numeric_level)

    # =======================
    # 🎨 Console Handler (colores)
    # =======================
    console_handler = colorlog.StreamHandler(sys.stdout)

    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s | "
        "%(cyan)s%(name)s%(reset)s | "
        "%(message)s "
        "%(blue)s[%(funcName)s]%(reset)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # =======================
    # 📁 File Handler (sin colores)
    # =======================
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | "
        "%(message)s [func:%(funcName)s]"
    )

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    root_logger.info("Logging system initialized")