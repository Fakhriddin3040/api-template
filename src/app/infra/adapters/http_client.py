import logging
from typing import Optional, Type
import httpx
from litestar import HttpMethod

from src.app.utils.environment.env_utils import DeploymentEnvironment
from src.app.application.ports.http_client_port import HttpClientProto
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import AppExceptionStatusCodes
from src.app.shared_kernel.ports.result import Result
from src.app.shared_kernel.types.base_types import T
from starlette import status

logger = logging.getLogger(__name__)


class HttpClient(HttpClientProto):

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            follow_redirects=True, verify=not DeploymentEnvironment.should_debug()
        )

    async def is_alive(self, host: str, timeout: int = 5, use_tls: bool = True) -> bool:
        """Ping the host to see if it's alive

        Args:
            use_tls (bool, optional): Whether or not to use TLS. Defaults to True.
            timeout (int, optional): Timeout in seconds. Defaults to 5.
            host (str): The host to check.

                Example:
                    1.1.1.1
                    domain.example.com

        Returns:
            bool: Whether or not the host is alive.
        """
        url = f"{'https' if use_tls else 'http'}://{host}"
        try:
            response = await self._client.head(url, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Is alife request for {host} completed successfully")
            return True

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            self._log_err(
                HttpMethod.GET,
                e,
                url,
                e.response if hasattr(e, "response") else None,
            )

        return False

    async def route_exists(
        self, url: str, timeout: int = 5, use_tls: bool = True
    ) -> bool:
        """Check if the url exists

        Args:
            use_tls (bool, optional): Whether or not to use TLS. Defaults to True.
            timeout (int, optional): Timeout in seconds. Defaults to 5.
            url (str): The ulr to check.

                Example:
                    domain.example.com/path/to/endpoint

        Returns:
            bool: Whether or not the host is alive.
        """
        full_url = f"{'https' if use_tls else 'http'}://{url}"

        try:
            response = await self._client.head(
                full_url,
                timeout=timeout,
            )

            if response.status_code != status.HTTP_404_NOT_FOUND:
                logger.info("Route exists", extra={"url": full_url})
                return True

            logger.info(
                "Route does not exist",
                extra={
                    "url": full_url,
                    "status_code": response.status_code,
                },
            )
            return False

        except (httpx.TimeoutException, httpx.RequestError) as e:
            self._log_err(
                HttpMethod.GET,
                e,
                e.repsonse.url if hasattr(e, "response") else None,
                self._get_response_from_exc(e),
            )

        return False

    def _log_err(
        self,
        method: HttpMethod,
        e: Exception,
        url: str,
        response: Optional[httpx.Response] = None,
        data: Optional[dict] = None,
        **payload,
    ) -> None:
        """Log error
        Args:
            method (HttpMethod): HTTP method
            e (Exception): Exception
            data (dict): Data to post.
            payload (dict): Payload data.
        """
        extra = {
            "payload": payload,
        }

        if data is not None:
            extra["data"] = data

        logger.error(
            f"Error on {method.name} to {url} with status code {response.status_code if response else 'undefined'}",
            extra=extra,
            exc_info=e,
        )

    def _get_response_from_exc(self, e: httpx.RequestError) -> Optional[httpx.Response]:
        return e.response if hasattr(e, "response") else None

    async def post(  # noqa
        self,
        url: str,
        data: dict,
        timeout: int = 5,
        use_tls: bool = True,
        dto: Type[T] = None,
        **headers: dict,
    ) -> Result[T, AppExceptionDetail]:
        """Post data to url
        Args:
            use_tls (bool, optional): Whether or not to use TLS. Defaults to True.
            data (dict): Data to post.
            timeout (int, optional): Timeout in seconds. Defaults to 5.
            url (str): The ulr to check.
            dto: Return data container type.
            Url Example:
                domain.example.com/path/to/endpoint
        """
        # url = url.replace("//", "/")
        full_url = f"{'https' if use_tls else 'http'}://{url}"

        try:
            logger.info(f"Post to {full_url}", extra={"payload": data})
            response = await self._client.post(
                full_url,
                json=data,
                timeout=timeout,
                headers=headers,
            )
            response.raise_for_status()

        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            self._log_err(HttpMethod.POST, e, url, e.response, data)
            return Result.err(
                AppExceptionDetail(
                    status=AppExceptionStatusCodes.UNEXPECTED_RESPONSE,
                    message=f"При запросе на хост '{url.split('/')[0]}', сервер ответил не так как ожидалось",
                )
            )

        except httpx.RequestError as e:
            self._log_err(HttpMethod.POST, e, url, None, data)
            return Result.err(
                AppExceptionDetail(
                    status=AppExceptionStatusCodes.UNEXPECTED_RESPONSE,
                    message=f"При запросе на хост '{url.split('/')[2]}' произошла неожиданная ошибка сети",
                )
            )

        try:
            return Result.ok(dto(**response.json()))
        except Exception as e:
            logger.error(
                "Error on decoding post request",
                exc_info=e,
                extra={"payload": data, "url": full_url},
            )
            return Result.err(
                AppExceptionDetail(
                    status=AppExceptionStatusCodes.UNEXPECTED_RESPONSE,
                    message="Ошибка при конвертации данных полученных с сервера",
                )
            )
