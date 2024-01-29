from typing import Optional

import aiohttp


async def call_api_with_status(method: str, path: str, body: Optional[dict] = None, headers: Optional[dict] = None):
    async with aiohttp.ClientSession() as session:
        if method == 'GET':
            response = await session.get(path, headers=headers)
            return response.status, await response.json()
        else:
            response = await session.post(path, json=body, headers=headers)
            return response.status, await response.json()


async def call_api(method: str, path: str, body: Optional[dict] = None, headers: Optional[dict] = None):
    return (await call_api_with_status(method, path, body, headers))[1]
