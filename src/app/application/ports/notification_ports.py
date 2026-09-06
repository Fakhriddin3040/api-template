from pathlib import Path
from typing import List, Optional, Protocol, runtime_checkable


@runtime_checkable
class EmailServiceProto(Protocol):
    async def send_email(
        self,
        dest: str | List[str],
        subject: str,
        content: str,
        subtype: str,
        attachments: Optional[List[Path | str]] = None,
    ) -> None: ...
