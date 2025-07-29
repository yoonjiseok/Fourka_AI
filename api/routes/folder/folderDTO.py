# api/routes/folder/folderDTO.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 폴더 생성을 위한 DTO
class FolderCreateDTO(BaseModel):
    name: str  # 폴더 이름
    company_id: int # 회사의 ID

# 폴더 이름 수정을 위한 DTO
class FolderUpdateDTO(BaseModel):
    folder_id: int # 수정할 폴더의 ID
    name: str      # 새로운 폴더 이름

# 폴더 삭제를 위한 DTO (POST 요청 바디 사용)
class FolderDeleteDTO(BaseModel):
    folder_id: int # 삭제할 폴더의 ID

# 회사별 폴더 조회를 위한 DTO (POST 요청 바디 사용)
class FolderGetByCompanyDTO(BaseModel):
    company_id: int # 조회할 회사의 ID

# 폴더 응답을 위한 DTO (데이터베이스 모델 기반)
class FolderResponseDTO(BaseModel):
    folder_id: int # 폴더 ID
    name: str      # 폴더 이름
    company_id: int # 회사의 ID
    created_at: datetime # 생성 시간

    class Config:
        from_attributes = True # SQLAlchemy 모델로부터 객체를 생성할 수 있도록 설정