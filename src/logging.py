import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    logger.remove()

    if json_logs:
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DDTHH:mm:ss.SSSZ} | {level} | {name}:{line} | {message}",
            level=log_level,
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for logger_name in [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn.lifespan",
        "uvicorn.server",
    ]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [InterceptHandler()]
        uvicorn_logger.propagate = False
