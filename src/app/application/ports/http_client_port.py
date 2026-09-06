from typing import Protocol, Type, runtime_checkable


from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.ports.result import Result
from src.app.shared_kernel.types.base_types import T


@runtime_checkable
class HttpClientProto(Protocol):
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
