from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class WalletStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


# Filters sorting


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class UserSortBy(str, Enum):
    ID = "id"
    EMAIL = "email"
    BALANCE = "balance"
    CREATED_AT = "created_at"


class AuctionStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
