from typing import Optional, Sequence, Any, List, Union, Dict, Self

from pydantic import Field, BaseModel

from src.app.shared_kernel.constants.enums import ModelFieldsBaseEnum
from src.app.shared_kernel.errors.constants import (
    AppExceptionStatusCodes,
    AppExceptionDetailCodes,
    AppExceptionMessage,
)


class AppExceptionDetail(BaseModel):
    status: AppExceptionStatusCodes
    code: Optional[AppExceptionDetailCodes] = None
    message: Optional[str] = None
    field: Optional[ModelFieldsBaseEnum | str] = None
    fields: Optional[Sequence[ModelFieldsBaseEnum | str]] = None
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    critical: Optional[bool] = False


class AppException(Exception):
    def __init__(
        self,
        message: str,
        details: Optional[Union[List[AppExceptionDetail], AppExceptionDetail]] = None,
        exception_status: Optional[AppExceptionStatusCodes] = None,
        status_code: Optional[int] = None,
    ):
        """
        :param details: Array of tuples describing the errors encountered
            indexes explains:
                1: Status codes from ApiExceptionStatusCodes
                2: Key value pair format
        :param exception_status: Optional exception status code from ApiExceptionStatusCodes
        :param status_code: Http default status code
        """
        has_error_details = details is not None
        self.details = None

        if not has_error_details and not exception_status:
            raise ValueError(
                "At least one of `details` or `exception_status` must be provided"
            )

        self.message = message
        self.status_code = status_code

        if not has_error_details:
            self.exception_status = exception_status
            return

        self.details = details

        if isinstance(details, AppExceptionDetail):
            details = [details]

        self.exception_status = AppExceptionStatusCodes.DETAILED_ERROR

        self.parsed_details = [item.model_dump(exclude_none=True) for item in details]

    def __str__(self):
        return f"ApiException: \nHttp status code: {self.status_code} \nException_status: {self.exception_status} \nDetails: {self.details}"

    def as_dict(self):
        result = {
            "message": self.message,
        }
        if self.exception_status:
            result.update({"exception_status": self.exception_status})

        if self.details:
            result.update({"details": self.details})

        return result

    @classmethod
    def from_details(cls, details: List[AppExceptionDetail]) -> Self:
        return cls(
            status_code=AppExceptionStatusCodes.DETAILED_ERROR,
            message=AppExceptionMessage.DETAILED_ERROR,
            details=details,
        )
