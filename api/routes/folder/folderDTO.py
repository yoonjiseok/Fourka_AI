from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# 폴더 생성을 위한 DTO
class FolderCreateDTO(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        description="폴더 이름 (공백일 수 없음)"
    )
    company_id: int # 회사의 ID

    @field_validator('name')
    @classmethod
    def name_must_not_be_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('폴더 이름은 공백일 수 없습니다.')
        return v

# 폴더 이름 수정을 위한 DTO
class FolderUpdateDTO(BaseModel):
    folder_id: int # 수정할 폴더의 ID
    name: str = Field(
        ...,
        min_length=1,
        description="새로운 폴더 이름(공백일 수 없음)"
    )

    @field_validator('name')
    @classmethod
    def name_must_not_be_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('폴더 이름은 공백일 수 없습니다.')
        return v

# 폴더 삭제를 위한 DTO
class FolderDeleteDTO(BaseModel):
    folder_id: int # 삭제할 폴더의 ID

# 폴더 응답을 위한 DTO (데이터베이스 모델 기반)
class FolderResponseDTO(BaseModel):
    folder_id: int # 폴더 ID
    name: str      # 폴더 이름
    company_id: int # 회사의 ID
    created_at: datetime # 생성 시간
    updated_at: datetime # 수정 시간

    class Config:
        from_attributes = True # SQLAlchemy 모델로부터 객체를 생성할 수 있도록 설정