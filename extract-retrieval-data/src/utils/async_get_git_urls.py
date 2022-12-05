import os
import asyncio

import httpx


async def async_get_git_urls(
    git_username: str, git_token: str, urls: list[str]
) -> list[httpx.Response]:
    """_summary_"""

    async def _async_get_git_url(client: httpx.AsyncClient, url: str) -> httpx.Response:
        response = await client.get(url, auth=(git_username, git_token))
        response.raise_for_status()
        return response

    async with httpx.AsyncClient() as client:
        tasks = (asyncio.create_task(_async_get_git_url(client, url)) for url in urls)
        return await asyncio.gather(*tasks)
