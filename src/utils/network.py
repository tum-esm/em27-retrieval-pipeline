import httpx
import asyncio


async def _get_git_url(
    client: httpx.AsyncClient, url: str, auth: tuple[str, str]
) -> httpx.Response:
    response = await client.get(url=url, auth=auth)
    response.raise_for_status()
    return response


async def get_git_urls(
    urls: list[str], git_username: str, git_token: str
) -> list[httpx.Response]:
    async with httpx.AsyncClient() as client:
        tasks = (
            asyncio.create_task(_get_git_url(client, url, (git_username, git_token)))
            for url in urls
        )
        return await asyncio.gather(*tasks)
