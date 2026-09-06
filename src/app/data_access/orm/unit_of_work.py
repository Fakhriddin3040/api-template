from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class OrmUnitOfWork(UnitOfWorkProto):
    def __init__(self, session: AsyncSession):
        self.db = session
        self._tx_began = self.db.in_transaction()  # transaction

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()

    async def __aenter__(self) -> Self:
        if not self._tx_began:
            self._tx_began = True

        return self

    async def flush(self) -> None:
        await self.db.flush()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_val:
                await self.db.rollback()
            else:
                await self.db.commit()
        finally:
            await self.db.close()


ensure_isimplementation(OrmUnitOfWork, UnitOfWorkProto)
