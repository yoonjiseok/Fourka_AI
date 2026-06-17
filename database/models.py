import datetime
import enum
from typing import List

from pgvector.sqlalchemy import Vector

from sqlalchemy import (
    ForeignKey,
    func,
    Enum,
    text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 1. Base 클래스 정의
class Base(DeclarativeBase):
    class Config:
        from_attributes = True
    pass


# 2. 공통 타임스탬프 Mixin 클래스 (Spring Boot의 BaseEntity 같은 역할)
class TimestampMixin:
    """모든 테이블에 공통으로 들어갈 타임스탬프 필드"""
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


# 2. 역할(Role)을 위한 Enum 클래스 정의
class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    Master = "master"


# 3. 피드백 타입을 위한 Enum 클래스 정의
class FeedbackType(enum.Enum):
    LIKE = "LIKE"
    UNLIKE = "UNLIKE"


# 3. 참조되는 모델들을 먼저 정의
class Company(Base, TimestampMixin):
    __tablename__ = "company"
    
    company_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    think_level: Mapped[int] = mapped_column(nullable=False, default=0)
    speech_level: Mapped[int] = mapped_column(nullable=False, default=0)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    logo_url: Mapped[str] = mapped_column(nullable=False)
    token: Mapped[str] = mapped_column(nullable=False)

    # 관계(relationship)
    departments: Mapped[List["Department"]] = relationship(back_populates="company")
    users: Mapped[List["User"]] = relationship(back_populates="company")
    folders: Mapped[List["Folder"]] = relationship(back_populates="company")
    tags: Mapped[List["Tag"]] = relationship(back_populates="company")
    faqs: Mapped[List["FAQ"]] = relationship(back_populates="company")


class Department(Base, TimestampMixin):
    __tablename__ = "department"
    
    department_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    
    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="departments")
    users: Mapped[List["User"]] = relationship(back_populates="department")


class User(Base, TimestampMixin):
    __tablename__ = "user"
    
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"))
    
    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="users")
    department: Mapped["Department"] = relationship(back_populates="users")
    chat_rooms: Mapped[List["ChatRoom"]] = relationship(secondary="user_chat_room", back_populates="participants")
    messages: Mapped[List["Chat"]] = relationship(back_populates="author")


class Folder(Base, TimestampMixin):
    __tablename__ = "folder"
    
    folder_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"))
    
    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="folders")
    documents: Mapped[List["Document"]] = relationship(back_populates="folder", cascade="all, delete-orphan")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    
    doc_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("folder.folder_id"), nullable=False)
    title: Mapped[str | None] = mapped_column()
    url: Mapped[str | None] = mapped_column()
    version: Mapped[str | None] = mapped_column()
    is_used: Mapped[bool] = mapped_column(default=False, nullable=False)
    commit_message: Mapped[str | None] = mapped_column()
    
    # 관계(relationship)
    folder: Mapped["Folder"] = relationship(back_populates="documents")
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base, TimestampMixin):
    __tablename__ = "chunk"
    
    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.doc_id"),primary_key=True, nullable=False)
    embedding: Mapped[list | None] = mapped_column(Vector(1024))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    weight: Mapped[float] = mapped_column(nullable=False, server_default=text("1.0"))

    # 관계(relationship)
    document: Mapped["Document"] = relationship(back_populates="chunks")


class ChatRoom(Base, TimestampMixin):
    __tablename__ = "chat_room"
    
    chat_room_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_room_name: Mapped[str | None] = mapped_column()
    
    # 관계(relationship)
    messages: Mapped[List["Chat"]] = relationship(back_populates="chat_room", cascade="all, delete-orphan")
    participants: Mapped[List["User"]] = relationship(secondary="user_chat_room", back_populates="chat_rooms")


class UserChatRoom(Base, TimestampMixin):
    __tablename__ = "user_chat_room"
    
    user_chat_room_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), primary_key=True)
    chat_room_id: Mapped[int] = mapped_column(ForeignKey("chat_room.chat_room_id"), primary_key=True)


class Chat(Base, TimestampMixin):
    __tablename__ = "chat"
    
    chat_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message: Mapped[str] = mapped_column(nullable=False)
    chat_room_id: Mapped[int] = mapped_column(ForeignKey("chat_room.chat_room_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    chunk_ids: Mapped[List] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    
    # 관계(relationship)    
    chat_room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    author: Mapped["User"] = relationship(back_populates="messages")
    feedback: Mapped[List["Feedback"]] = relationship(back_populates="chat")


# 6. Tag 모델 추가
class Tag(Base, TimestampMixin):
    __tablename__ = "tag"

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"), nullable=False)

    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="tags")
    faqs: Mapped[List["FAQ"]] = relationship(back_populates="tag")


# 7. FAQ 모델 추가
class FAQ(Base, TimestampMixin):
    __tablename__ = "faq"

    faq_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.company_id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey(Tag.tag_id), nullable=False)

    # 관계(relationship)
    company: Mapped["Company"] = relationship(back_populates="faqs")
    tag: Mapped["Tag"] = relationship(back_populates="faqs")


# 8. Feedback 모델 추가
class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.chat_id"), nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), nullable=False)
    answer: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)

    # 관계(relationship)
    chat: Mapped["Chat"] = relationship(back_populates="feedback")