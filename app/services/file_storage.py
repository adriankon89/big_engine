from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save(self, storage_key: str, content: bytes) -> None: ...

    def delete(self, storage_key: str) -> None: ...


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, storage_key: str, content: bytes) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / storage_key).write_bytes(content)

    def delete(self, storage_key: str) -> None:
        (self.root / storage_key).unlink(missing_ok=True)
