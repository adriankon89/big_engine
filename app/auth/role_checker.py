from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.core.exceptions import NoPermissionException


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        user_role = current_user.get("role")
        if user_role not in self.allowed_roles:
            raise NoPermissionException("Access denied")
        return current_user
