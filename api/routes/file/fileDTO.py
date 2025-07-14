from pydantic import BaseModel


class UpdateDTO(BaseModel):
    doc_id: int
    title: str

class folderDTO(BaseModel):
    folder_id: int