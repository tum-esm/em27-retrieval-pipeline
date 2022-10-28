import httpx
import asyncio


async def git_request(urls: list[str], git_username:str, git_token:str) -> list[httpx.Response]:
            async with httpx.AsyncClient() as client:
                requests = (
                    client.get(
                        url=url,
                        auth=(git_username, git_token),
                        timeout=10,
                    )
                    for url in urls
                )
                return await asyncio.gather(*requests)