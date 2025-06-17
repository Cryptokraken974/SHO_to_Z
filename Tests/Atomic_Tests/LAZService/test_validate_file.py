import asyncio
import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

try:
    import aiohttp  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without aiohttp
    aiohttp_stub = types.ModuleType('aiohttp')

    class _CS:
        def __init__(self, *a, **k):
            pass
        async def request(self, *a, **k):
            class R:
                status = 200
                async def json(self):
                    return {}
                async def text(self):
                    return ''
                @property
                def closed(self):
                    return False
            return R()
        async def close(self):
            pass

    class _CT:
        def __init__(self, total=0):
            pass

    aiohttp_stub.ClientSession = _CS
    aiohttp_stub.ClientTimeout = _CT
    aiohttp_stub.FormData = object
    aiohttp_stub.ContentTypeError = Exception
    sys.modules.setdefault('aiohttp', aiohttp_stub)

from app.api.laz_service import LAZService

service = LAZService(base_url=os.getenv('SERVICE_BASE_URL', 'http://localhost:8000'))

async def run_test():
    await service.validate_file('demo.laz')

if __name__ == '__main__':
    asyncio.run(run_test())
