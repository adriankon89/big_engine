from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UploadedFileDTO:
    filename: str
    content_type: str
    content: bytes
