import httpx
import asyncio
import random
from datetime import datetime
from app.config.setting import PAYMENT_API_URL, PROTECTION_API_URL
from app.schemas import PaymentQuote, ProtectionQuote


class ExternalApiError(Exception):
    pass


class BaseHttpxClient:
    def __init__(
        self,
        base_url: str,
        timeout: float | httpx.Timeout,
        headers: dict[str, str] | None = None,
        rate_limit_requests: int | None = None,
        rate_limit_interval: int | None = None,
        retry_count: int = 2,
    ) -> None:
        if rate_limit_requests is not None and rate_limit_interval is None:
            raise ValueError(
                "rate_limit_interval is required when rate_limit_requests is set"
            )

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )
        self.rate_limit_requests = rate_limit_requests
        self.retry_count = max(1, retry_count)
        self._rate_limit_interval = rate_limit_interval

        if rate_limit_requests is not None:
            self._rate_limiter = asyncio.Semaphore(rate_limit_requests)
        else:
            self._rate_limiter = None

    async def close(self) -> None:
        await self._client.aclose()

    async def _release_rate_limiter_later(self) -> None:
        if self._rate_limiter is None or self._rate_limit_interval is None:
            return

        await asyncio.sleep(self._rate_limit_interval + 0.05)
        self._rate_limiter.release()

    async def _exponential_backoff_sleep(self, attempt: int) -> None:
        delay = 0.5 * 2 ** (attempt + 1)
        jitter = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay + jitter)

    async def request(
        self,
        method: str,
        url: str,
        retry: bool = False,
        **kwargs,
    ) -> httpx.Response | None:
        attempts = self.retry_count if retry else 1

        for attempt in range(attempts):
            if self._rate_limiter is not None:
                await self._rate_limiter.acquire()
                asyncio.create_task(self._release_rate_limiter_later())

            try:
                response = await self._client.request(method, url, **kwargs)
            except httpx.RequestError:
                if attempt == attempts - 1:
                    raise

                await self._exponential_backoff_sleep(attempt)
                continue

            if (
                response.status_code not in (429, 503, 500) or
                attempt == attempts - 1
            ):
                return response

            await self._exponential_backoff_sleep(attempt)


class ProtectionClient(BaseHttpxClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=PROTECTION_API_URL,
            timeout=httpx.Timeout(3.0),
        )

    async def calculate(
        self,
        booking_id: int,
        ticket_amount: int,
        event_category: str,
        event_starts_at: datetime,
    ) -> ProtectionQuote | None:
        payload = {
            "booking_id": booking_id,
            "ticket_amount": ticket_amount,
            "event_category": event_category,
            "event_starts_at": event_starts_at.isoformat(),
        }

        try:
            async with asyncio.timeout(3.0):
                response = await self.request(
                    "POST", "/protection/calculate", json=payload
                )

            if response.status_code >= 500:
                return None

            response.raise_for_status()
            return ProtectionQuote.model_validate(response.json())
        except (TimeoutError, httpx.HTTPError):
            return None


class PaymentClient(BaseHttpxClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=PAYMENT_API_URL,
            timeout=httpx.Timeout(2.0, connect=1.0),
        )

    async def calculate(
        self,
        booking_id: int,
        amount: int,
        max_attempts: int = 3,
    ) -> PaymentQuote:
        payload = {
            "booking_id": booking_id,
            "amount": amount,
            "currency": "KGS",
        }

        for attempt in range(1, max_attempts + 1):
            try:
                response = await self.request(
                    "POST", "/payment/calculate", json=payload
                )

                if response.status_code == 429 and attempt < max_attempts:
                    await asyncio.sleep(_retry_delay(attempt))
                    continue

                response.raise_for_status()
                return PaymentQuote.model_validate(response.json())
            except httpx.RequestError as exc:
                if attempt == max_attempts:
                    raise ExternalApiError("Payment API is unavailable") from exc
                await asyncio.sleep(_retry_delay(attempt))
            except httpx.HTTPStatusError as exc:
                raise ExternalApiError("Payment API returned an error") from exc

        raise ExternalApiError("Payment API retry attempts exhausted")


payment_client = PaymentClient()
protection_client = ProtectionClient()


async def close_httpx_clients() -> None:
    await payment_client.close()
    await protection_client.close()


def _retry_delay(attempt: int) -> float:
    backoff = min(0.2 * 2 ** (attempt - 1), 1.5)
    jitter = random.uniform(0, 0.2)
    return backoff + jitter
