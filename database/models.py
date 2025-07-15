import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


# 1. 모든 모델이 상속할 Base 클래스 정의
class Base(DeclarativeBase):
    pass


# 2. Company 모델 추가
class Company(Base):
    __tablename__ = "company"

    company_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())


# 3. Document_folder 모델 수정
class Folder(Base):
    __tablename__ = "folder"

    # Mapped 타입 힌트 추가 및 mapped_column 사용
    folder_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    documents: Mapped[List["Document"]] = relationship(back_populates="folder")


# 4. Document 모델 수정
class Document(Base):
    """'document' 테이블과 매핑될 document 모델"""
    __tablename__ = "documents"

    # Column -> mapped_column으로 변경하고 Mapped 타입 힌트 추가
    doc_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey(Folder.folder_id), nullable=False)
    title: Mapped[str | None] = mapped_column() # nullable=True는 | None으로 표현
    url: Mapped[str | None] = mapped_column()
    version: Mapped[str | None] = mapped_column() 
    is_used: Mapped[bool] = mapped_column(default=False)
    commit_message: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    folder: Mapped["Folder"] = relationship(back_populates="documents")
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


# 5. Chunk 모델 수정
class Chunk(Base):
    __tablename__ = "chunk"

    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey(Document.doc_id))
    doc_folder_id: Mapped[int] = mapped_column(ForeignKey(Folder.folder_id))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("company.company_id"))
    chunk_index: Mapped[int] = mapped_column(default=0)
    embedding: Mapped[list | None] = mapped_column(Vector) # Vector 타입은 리스트로 표현
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    # 관계(relationship)도 Mapped로 감싸줍니다.
    document: Mapped["Document"] = relationship(back_populates="chunks")