from typing import Any

from sqlalchemy import ColumnExpressionArgument, or_

from src.app.data_access.orm.adapters.filter_compilers import SqlAlchemyFiltersCompiler
from src.app.data_access.orm.identity.models.user_orm_model import UserOrmModel
from src.app.modules.filtering.types import FilterContainer


class UserFilterCompiler(SqlAlchemyFiltersCompiler[UserOrmModel]):
    def compile_search__eq(
        self, container: FilterContainer
    ) -> ColumnExpressionArgument[Any]:
        # Prefix match (`value%`), not `%value%`: it can use a text_pattern_ops
        # index, and a contains-match on every user column does not scale.
        pattern = f"{container.value}%"

        return or_(
            self.model.first_name.ilike(pattern),
            self.model.last_name.ilike(pattern),
            self.model.email.ilike(pattern),
        )
