import aiofiles
import os

async def save_file_async(file, storage_directory):
    """
    Save an uploaded file asynchronously.

    Parameters:
    - file: UploadFile - The uploaded file.
    - storage_directory: str - The directory where the file should be saved.
    """
    # Remove any previous files in the directory
    for filename in os.listdir(storage_directory):
        file_path = os.path.join(storage_directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Save the current file
    file_path = os.path.join(storage_directory, file.filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)