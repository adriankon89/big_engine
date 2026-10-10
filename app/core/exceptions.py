class UserAlreadyExistsError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} already exists")


class InvalidTokenError(Exception):
    def __init__(self, message: str = "Invalid or expired token"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(Exception):
    def __init__(self, identifier: str | int):
        self.identifier = identifier
        super().__init__(f"User '{identifier}' was not found.")


class InvalidCredentialsException(Exception):
    def __init__(self, message: str = "Invalid email or password"):
        self.message = message
        super().__init__(self.message)


class BadRequestException(Exception):
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedException(Exception):
    def __init__(self, message: str = "Wrong credentials"):
        self.message = message
        super().__init__(self.message)


class NoPermissionException(Exception):
    def __init__(self, message: str = "No permission"):
        self.message = message
        super().__init__(self.message)
