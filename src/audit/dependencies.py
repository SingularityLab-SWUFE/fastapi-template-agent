import uuid

from fastapi import Request


async def generate_request_id(request: Request) -> str:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id
