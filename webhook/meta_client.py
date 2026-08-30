import asyncio

import httpx

from config import settings
from logger import logger

GRAPH_URL = f"https://graph.facebook.com/{settings.meta_api_version}"

AUTH_ERROR_CODES = {190, 102, 200, 10}


class MetaAPIError(Exception):
    def __init__(self, message: str, is_auth_error: bool = False):
        super().__init__(message)
        self.is_auth_error = is_auth_error


async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GRAPH_URL}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": settings.meta_redirect_uri,
                "code": code,
            },
        )
        data = resp.json()
        if resp.status_code != 200:
            raise MetaAPIError(f"Ошибка обмена code на access_token: {data}")
        return data


async def get_long_lived_token(short_token: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GRAPH_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        data = resp.json()
        if resp.status_code != 200:
            raise MetaAPIError(f"Ошибка получения долгоживущего токена: {data}")
        return data


async def get_ig_business_account(access_token: str) -> dict:
    """Находит первую Facebook-страницу пользователя со связанным
    Instagram Business/Creator аккаунтом и возвращает его данные.

    Примечание: если у пользователя несколько Facebook-страниц с разными
    привязанными Instagram-аккаунтами, для полноценного выбора нужного
    аккаунта потребуется дополнительный шаг выбора в боте — здесь взят
    первый найденный вариант как самый частый случай.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        pages_resp = await client.get(f"{GRAPH_URL}/me/accounts", params={"access_token": access_token})
        pages = pages_resp.json()
        if pages_resp.status_code != 200:
            raise MetaAPIError(f"Ошибка получения списка Facebook-страниц: {pages}")

        for page in pages.get("data", []):
            page_id = page["id"]
            page_token = page.get("access_token", access_token)
            ig_resp = await client.get(
                f"{GRAPH_URL}/{page_id}",
                params={"fields": "instagram_business_account", "access_token": page_token},
            )
            ig_data = ig_resp.json()
            ig_account = ig_data.get("instagram_business_account")
            if not ig_account:
                continue
            ig_id = ig_account["id"]
            info_resp = await client.get(
                f"{GRAPH_URL}/{ig_id}",
                params={"fields": "username", "access_token": page_token},
            )
            info = info_resp.json()
            return {
                "ig_user_id": ig_id,
                "username": info.get("username", ig_id),
                "access_token": page_token,
            }

        raise MetaAPIError("Не найден Instagram Business/Creator аккаунт, привязанный к вашим Facebook-страницам.")


async def send_private_reply(comment_id: str, message: str, access_token: str, max_retries: int = 3) -> None:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{GRAPH_URL}/{comment_id}/private_replies",
                    params={"access_token": access_token},
                    json={"message": message},
                )
                data = resp.json()
                if resp.status_code == 200:
                    return
                error = data.get("error", {})
                code = error.get("code")
                if code in AUTH_ERROR_CODES:
                    raise MetaAPIError(str(error), is_auth_error=True)
                last_error = MetaAPIError(str(error))
        except MetaAPIError as e:
            if e.is_auth_error:
                raise
            last_error = e
        except httpx.HTTPError as e:
            last_error = e

        logger.warning(f"Private reply попытка {attempt}/{max_retries} не удалась для {comment_id}: {last_error}")
        if attempt < max_retries:
            await asyncio.sleep(2 * attempt)

    raise last_error