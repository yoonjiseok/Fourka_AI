import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. 모든 모델이 상속할 Base 클래스 정의
class Base(DeclarativeBase):
    pass


# 2. Document_folder 모델 수정
class Document_folder(Base):
    __tablename__ = "document_folder"

    # Mapped 타입 힌트 추가 및 mapped_column 사용
    doc_folder_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("Company.company_id"))
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    documents: Mapped[List["Document"]] = relationship(back_populates="folder")


# 3. Document 모델 수정
class Document(Base):
    """'document' 테이블과 매핑될 document 모델"""
    __tablename__ = "documents"

    # Column -> mapped_column으로 변경하고 Mapped 타입 힌트 추가
    doc_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_folder_id: Mapped[int] = mapped_column(ForeignKey(Document_folder.doc_folder_id), nullable=False)
    title: Mapped[str | None] = mapped_column() # nullable=True는 | None으로 표현
    url: Mapped[str | None] = mapped_column()
    Field: Mapped[str | None] = mapped_column() # 버전
    is_used: Mapped[bool] = mapped_column(default=False)
    commit_message: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    folder: Mapped["Document_folder"] = relationship(back_populates="documents")
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


# 4. Chunk 모델 수정
class Chunk(Base):
    __tablename__ = "chunk"

    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey(Document.doc_id))
    doc_folder_id: Mapped[int] = mapped_column(ForeignKey(Document_folder.doc_folder_id))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("Company.company_id"))
    chunk_index: Mapped[int] = mapped_column(default=0)
    embedding: Mapped[list | None] = mapped_column(Vector) # Vector 타입은 리스트로 표현
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    document: Mapped["Document"] = relationship(back_populates="chunks")