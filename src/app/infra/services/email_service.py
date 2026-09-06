import asyncio
import logging
import mimetypes
from collections import deque
from os import PathLike

import aiosmtplib
from email.message import EmailMessage

from pathlib import Path
from typing import List, Deque, Coroutine, Optional

from src.app.application.ports.notification_ports import EmailServiceProto
from src.app.shared_kernel.config.infra_configs import SmtpConfig
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

logger = logging.getLogger(__name__)


class EmailService(EmailServiceProto):
    """
    Email notification service for sending emails.

    Args:
        smtp_config: SMTP configuration

    Notes:
        Some methods must not raise any exceptions where is signed with the InProcessEventHandler.
            If exception occurs while processing business login/event, this class methods should not
            raise an exception.
    """

    def __init__(self, smtp_config: SmtpConfig) -> None:
        self._config = smtp_config

    async def send_email(
        self,
        dest: str | List[str],
        subject: str,
        content: str,
        subtype: str,
        attachments: Optional[List[Path | str]] = None,
    ) -> None:
        dest = dest if not isinstance(dest, str) else [dest]

        if isinstance(attachments, (str, PathLike)):
            attachments = [attachments]

        tasks: Deque[Coroutine] = deque()

        for d in dest:
            message = EmailMessage()
            message["From"] = f"Anbor <{self._config.username}> "
            message["To"] = d
            message["Subject"] = subject
            message.set_content(
                content, subtype=subtype
            )  # need to fix the verification code

            if attachments:
                await self._add_attachments(message, attachments)

            tasks.append(self._send_email(message))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for d, result in zip(dest, results, strict=True):
            if isinstance(result, Exception):
                logger.error(
                    "Email sent failed with error",
                    extra={
                        "recipient": d,
                        "subject": subject,
                    },
                    exc_info=result,
                )

    async def _send_email(self, message: EmailMessage) -> None:
        await aiosmtplib.send(
            message,
            hostname=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
            use_tls=self._config.port == 465,
            start_tls=self._config.port == 587,
            timeout=self._config.timeout,
        )

    async def _add_attachments(
        self, msg: EmailMessage, attachments: List[PathLike | str]
    ) -> None:
        for attachment in attachments:
            path = Path(attachment)

            ctype, encoding = mimetypes.guess_type(str(path))

            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"

            maintype, subtype = ctype.split("/", 1)

            data = await asyncio.to_thread(path.read_bytes)
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=path.name
            )


ensure_isimplementation(EmailService, EmailServiceProto)
