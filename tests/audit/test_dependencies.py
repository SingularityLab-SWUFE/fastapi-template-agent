import uuid
from unittest.mock import MagicMock

import pytest

from src.audit.dependencies import generate_request_id


@pytest.mark.asyncio
async def test_generate_request_id():
    request = MagicMock()
    request.state = MagicMock()

    request_id = await generate_request_id(request)

    assert request_id is not None
    assert isinstance(request_id, str)
    assert uuid.UUID(request_id)
    assert request.state.request_id == request_id


@pytest.mark.asyncio
async def test_generate_request_id_unique():
    request1 = MagicMock()
    request1.state = MagicMock()
    request2 = MagicMock()
    request2.state = MagicMock()

    request_id1 = await generate_request_id(request1)
    request_id2 = await generate_request_id(request2)

    assert request_id1 != request_id2
