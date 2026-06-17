from pydantic import BaseModel


class UpdateDTO(BaseModel):
    doc_id: int
    title: str

class UploadDTO(BaseModel):
    title: str
    version : str
    folder_id : int
    commit_message : str

class DeleteDTO(BaseModel):
    doc_id: int

class folderDTO(BaseModel):
    folder_id: int

class ChangeMainDocumentDTO(BaseModel):
    folder_id: int
    doc_id: int
