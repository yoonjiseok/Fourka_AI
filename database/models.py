import datetime
import enum
from typing import List

from pgvector.sqlalchemy import Vector

from sqlalchemy import (
    ForeignKey,
    func,
    Enum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. Base 클래스 정의
class Base(DeclarativeBase):
    class Config:
        from_attributes = True
    pass


# 2. 역할(Role)을 위한 Enum 클래스 정의
class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    Master = "master"


# 3. 참조되는 모델들을 먼저 정의
class Company(Base):
    __tablename__ = "company"
    
    company_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    departments: Mapped[List["Department"]] = relationship(back_populates="company")
    users: Mapped[List["User"]] = relationship(back_populates="company")
    folders: Mapped[List["Folder"]] = relationship(back_populates="company")
    tags: Mapped[List["Tag"]] = relationship(back_populates="company")
    faqs: Mapped[List["FAQ"]] = relationship(back_populates="company")


class Department(Base):
    __tablename__ = "department"
    
    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    company: Mapped["Company"] = relationship(back_populates="departments")
    users: Mapped[List["User"]] = relationship(back_populates="department")


class User(Base):
    __tablename__ = "user"
    
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    password: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"))
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    company: Mapped["Company"] = relationship(back_populates="users")
    department: Mapped["Department"] = relationship(back_populates="users")
    chat_rooms: Mapped[List["ChatRoom"]] = relationship(secondary="user_chat_room", back_populates="participants")
    messages: Mapped[List["Chat"]] = relationship(back_populates="author")


class Folder(Base):
    __tablename__ = "folder"
    
    folder_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    company: Mapped["Company"] = relationship(back_populates="folders")
    documents: Mapped[List["Document"]] = relationship(back_populates="folder", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    doc_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("folder.folder_id"), nullable=False)
    title: Mapped[str | None] = mapped_column()
    url: Mapped[str | None] = mapped_column()
    version: Mapped[str | None] = mapped_column()
    is_used: Mapped[bool] = mapped_column(default=False, nullable=False)
    commit_message: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    folder: Mapped["Folder"] = relationship(back_populates="documents")
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunk"
    
    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.doc_id"), nullable=False)
    embedding: Mapped[list | None] = mapped_column(Vector(768))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    document: Mapped["Document"] = relationship(back_populates="chunks")


class ChatRoom(Base):
    __tablename__ = "chat_room"
    
    chat_room_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_room_name: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    messages: Mapped[List["Chat"]] = relationship(back_populates="chat_room", cascade="all, delete-orphan")
    participants: Mapped[List["User"]] = relationship(secondary="user_chat_room", back_populates="chat_rooms")


class UserChatRoom(Base):
    __tablename__ = "user_chat_room"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    chat_room_id: Mapped[int] = mapped_column(ForeignKey("chat_room.chat_room_id"), primary_key=True)


class Chat(Base):
    __tablename__ = "chat"
    
    chat_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message: Mapped[str] = mapped_column(nullable=False)
    chat_room_id: Mapped[int] = mapped_column(ForeignKey("chat_room.chat_room_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    
    chat_room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    author: Mapped["User"] = relationship(back_populates="messages")


# 6. Tag 모델 추가
class Tag(Base):
    __tablename__ = "tag"

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())

    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="tags")
    faqs: Mapped[List["FAQ"]] = relationship(back_populates="tag")


# 7. FAQ 모델 추가
class FAQ(Base):
    __tablename__ = "faq"

    faq_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[list | None] = mapped_column(Vector(768))  # 질문 임베딩
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey(Tag.tag_id), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())

    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="faqs")
    tag: Mapped["Tag"] = relationship(back_populates="faqs")