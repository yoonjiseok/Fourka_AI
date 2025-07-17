from database.repository import file_repository
from database.repository.file_repository import FileRepository

class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository

    async def update_file_name(self, file_id: int, title: str):
            await self.file_repository.update_file_name(file_id, title)

    async def get_all_versions(self, folder_id: int):
        return await self.file_repository.get_all_versions_by_folder_id(folder_id)