import pytest
from fastapi import HTTPException
from src.decorators.api_response import api_response
from src.responses import JsonResponse


def test_sync_function_wrapping():
    """测试同步函数包裹"""
    @api_response
    def sync_func() -> str:
        return "test data"

    result = sync_func()
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.code == 200
    assert result.data == "test data"
    assert result.error is None


@pytest.mark.asyncio
async def test_async_function_wrapping():
    """测试异步函数包裹"""
    @api_response
    async def async_func() -> str:
        return "async data"

    result = await async_func()
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.code == 200
    assert result.data == "async data"
    assert result.error is None


def test_sync_function_with_args():
    """测试带参数的同步函数"""
    @api_response
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.data == 5


@pytest.mark.asyncio
async def test_async_function_with_args():
    """测试带参数的异步函数"""
    @api_response
    async def multiply(x: int, y: int) -> int:
        return x * y

    result = await multiply(4, 5)
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.data == 20


def test_already_json_response():
    """测试已经是JsonResponse的返回值不重复包裹"""
    original_response = JsonResponse.success("pre-wrapped")

    @api_response
    def returns_json_response() -> JsonResponse[str]:
        return original_response

    result = returns_json_response()
    # 应该是同一个对象（避免重复包裹）
    assert result is original_response
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.data == "pre-wrapped"


@pytest.mark.asyncio
async def test_async_already_json_response():
    """测试异步函数返回JsonResponse不重复包裹"""
    original_response = JsonResponse.success("async pre-wrapped")

    @api_response
    async def returns_json_response() -> JsonResponse[str]:
        return original_response

    result = await returns_json_response()
    assert result is original_response
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.data == "async pre-wrapped"


def test_sync_exception_handling():
    """测试同步函数异常处理"""
    @api_response
    def raises_exception() -> str:
        raise ValueError("Something went wrong")

    result = raises_exception()
    assert isinstance(result, JsonResponse)
    assert result.success is False
    assert result.code == 50000  # 默认错误码
    assert result.data is None
    assert result.error is not None
    assert "Something went wrong" in result.error["msg"]


def test_http_exception_handling():
    """测试HTTP异常处理"""
    @api_response
    def raises_http_exception() -> str:
        raise HTTPException(status_code=404, detail="Not found")

    result = raises_http_exception()
    assert isinstance(result, JsonResponse)
    assert result.success is False
    assert result.code == 40400  # 404 * 100
    assert result.data is None
    assert result.error is not None
    assert "Not found" in result.error["msg"]


@pytest.mark.asyncio
async def test_async_exception_handling():
    """测试异步函数异常处理"""
    @api_response
    async def raises_async_exception() -> str:
        raise RuntimeError("Async error")

    result = await raises_async_exception()
    assert isinstance(result, JsonResponse)
    assert result.success is False
    assert result.code == 50000
    assert result.data is None
    assert result.error is not None
    assert "Async error" in result.error["msg"]


def test_none_return_value():
    """测试返回None值"""
    @api_response
    def returns_none() -> None:
        return None

    result = returns_none()
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.code == 200
    assert result.data is None
    assert result.error is None


@pytest.mark.asyncio
async def test_async_none_return_value():
    """测试异步函数返回None值"""
    @api_response
    async def returns_none() -> None:
        return None

    result = await returns_none()
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.code == 200
    assert result.data is None
    assert result.error is None


def test_complex_data_structure():
    """测试复杂数据结构"""
    complex_data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "total": 2
    }

    @api_response
    def returns_complex() -> dict:
        return complex_data

    result = returns_complex()
    assert isinstance(result, JsonResponse)
    assert result.success is True
    assert result.data == complex_data


def test_decorator_preserves_function_name():
    """测试装饰器保持函数名"""
    @api_response
    def original_function() -> str:
        """原始函数文档"""
        return "test"

    assert original_function.__name__ == "original_function"
    assert original_function.__doc__ == "原始函数文档"