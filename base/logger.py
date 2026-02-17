import logging
import sys
import time
from typing import Optional

import coloredlogs


logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("stem").setLevel(logging.WARNING)

FILE_FORMAT = "[{levelname:^8}] [{elapsed}]: {message}"
CONSOLE_FORMAT = "[%(levelname)s] [%(elapsed)s]: %(message)s"
FIELD_STYLES = dict(
    elapsed=dict(color="green", bold=True),
)


class _DefaultElapsedFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "elapsed"):
            record.elapsed = "-"
        return True


class ElapsedLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        start_time = self.extra.get("start_time")
        if start_time is None:
            extra.setdefault("elapsed", "-")
        else:
            extra.setdefault("elapsed", f"{time.perf_counter() - start_time:10.2f}s")
        return msg, kwargs


def configure_logging(
    *,
    debugging: bool = False,
    file_log_path: str,
    results: bool = False
) -> logging.Logger:
    logger = logging.getLogger()
    if getattr(logger, "_mao_configured", False):
        return logger

    logger.setLevel(logging.DEBUG)
    elapsed_filter = _DefaultElapsedFilter()

    coloredlogs.install(
        level=25 if results else (logging.DEBUG if debugging else logging.INFO),
        logger=logger,
        fmt=CONSOLE_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        field_styles=FIELD_STYLES,
    )

    for handler in logger.handlers:
        handler.addFilter(elapsed_filter)

    file_formatter = logging.Formatter(
        fmt=FILE_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )

    file_handler = logging.FileHandler(file_log_path, encoding="utf-8", mode="w")
    file_handler.setLevel(25 if results else logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(elapsed_filter)

    logger.addHandler(file_handler)
    logger._mao_configured = True
    return logger


def get_elapsed_logger(start_time: float, file_log_path: str, debugging: bool, results: bool = False, name: Optional[str] = None) -> ElapsedLoggerAdapter:
    configure_logging(file_log_path=file_log_path, debugging=debugging, results=results)
    return ElapsedLoggerAdapter(logging.getLogger(name), {"start_time": start_time})


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    configure_logging().error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = handle_exception
