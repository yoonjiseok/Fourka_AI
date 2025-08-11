from datetime import datetime
from pydantic import BaseModel


# FAQ 관련 DTO
class FAQCreateDTO(BaseModel):
    question: str
    answer: str
    tag_id: int


class FAQUpdateDTO(BaseModel):
    faq_id: int
    question: str
    answer: str
    tag_id: int


class FAQDeleteDTO(BaseModel):
    faq_id: int


class FAQResponseDTO(BaseModel):
    faq_id: int
    question: str
    answer: str
    company_id: int
    tag_id: int
    tag_name: str
    created_at: datetime


# Tag 관련 DTO
class TagCreateDTO(BaseModel):
    name: str
    company_id: int


class TagResponseDTO(BaseModel):
    tag_id: int
    name: str
    company_id: int
    created_at: datetime 