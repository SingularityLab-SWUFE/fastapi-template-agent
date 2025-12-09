from fastapi import FastAPI
from src.exceptions import BusinessException
from src.responses import ResponseWrapperMiddleware
from src.handlers import register_exception_handlers
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(ResponseWrapperMiddleware)
register_exception_handlers(app)

class TestBusinessException(BusinessException):
    pass

class ExampleResponse(BaseModel):
    content: str

@app.get("/test-exception")
async def test():
    import random
    random_number = random.randint(1, 100)
    if random_number % 2 == 0:
        raise TestBusinessException(code=400, msg="This is a test business exception")
    else:
        return ExampleResponse(content="This is a successful response")

@app.post("/auth/jwt/login")
async def login_test():
    raise BusinessException(code=401, msg="Invalid credentials")
