from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.get("/test-logging")
async def test_logging():
    logger.info("Application logger test")
    logger.bind(action="test", resource_type="logging", result="success").info(
        "Audit logger test"
    )

    return {"message": "Check logs for output"}


@router.get("/test-logging-error")
async def test_logging_error():
    try:
        raise ValueError("Intentional test error")
    except ValueError:
        logger.exception("Exception logged with traceback")
        return {"message": "Exception logged, check logs"}
