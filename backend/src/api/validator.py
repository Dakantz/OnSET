from fastapi import HTTPException, UploadFile, status


async def validate_image_file(file: UploadFile) -> bool:
    # Check file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Only JPEG and PNG are allowed.",
        )

    # Check file size (2MB max)
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

    # Reset file position
    await file.seek(0)

    # Read file in chunks to check size
    file_size = 0
    while chunk := await file.read(8192):  # Read in 8KB chunks
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size allowed is 2MB.",
            )

    # Reset file position for later use
    await file.seek(0)
    return True
