from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: Annotated[dict, Depends(get_current_user)]
    ) -> dict:
        user_role = current_user.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        return current_user
