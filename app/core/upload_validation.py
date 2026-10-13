from collections.abc import Sequence
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.exceptions import UploadValidationError

MEBIBYTE = 1024 * 1024


@dataclass(frozen=True)
class UploadPolicy:
    max_files: int
    max_file_size_bytes: int
    allowed_signatures: tuple[bytes, ...]
    allowed_formats: str


IMAGE_UPLOAD_POLICY = UploadPolicy(
    max_files=5,
    max_file_size_bytes=5 * MEBIBYTE,
    allowed_signatures=(b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff"),
    allowed_formats="PNG and JPEG",
)


def validate_uploads(uploads: Sequence[UploadFile], *, policy: UploadPolicy) -> None:
    if len(uploads) > policy.max_files:
        raise UploadValidationError(
            f"A maximum of {policy.max_files} files is allowed."
        )

    for upload in uploads:
        upload.file.seek(0, 2)
        file_size = upload.file.tell()
        upload.file.seek(0)

        if file_size > policy.max_file_size_bytes:
            max_size_mb = policy.max_file_size_bytes // MEBIBYTE
            raise UploadValidationError(
                f"Each file must be no larger than {max_size_mb} MB."
            )

        signature = upload.file.read(max(map(len, policy.allowed_signatures)))
        upload.file.seek(0)
        if not signature.startswith(policy.allowed_signatures):
            raise UploadValidationError(
                f"Only {policy.allowed_formats} files are allowed."
            )
