from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


# 모든 모델이 상속받을 기본 클래스
class Base(DeclarativeBase):
    pass

class Document_folder(Base, description="docunet_folder'와 매핑될 document_folder 모델"):
    __tablename__ = "document_folder"

    doc_folder_id = Column(Integer, primary_key=True, autoincrement=True, )
    company_id = Column(Integer, ForeignKey("Company.company_id"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    documents: "List[Document]" = relationship("Document", back_populates="folder", description="이 폴더에 속한 모든 Document 객체에 접근 가능")


class Document(Base, description="'document' 테이블과 매핑될 document 모델"):
    __tablename__ = "document"  # 데이터베이스에 생성될 테이블 이름

    doc_id = Column(Integer, primary_key=True, autoincrement=True, description="문서의 ID")
    doc_folder_id = Column(Integer, ForeignKey(Document_folder.doc_folder_id), nullable=False)
    title = Column(String, nullable=True, description="문서 제목")
    url = Column(String, nullable=True, description="S3주소")
    Field = Column(String, nullable=True, description="버전")
    is_used = Column(Boolean, nullable=False, default=False, description="사용 유무, 하나의 파일을 제외하고는 모두 False")
    commit_message = Column(String, nullable=True, description="파일과 함께 올라올 수 있는 수정 메시지")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), description="생성일")

    # back_populates는 양방향 관계로 만들어줌
    folder: "Document_folder" = relationship("Document_folder", back_populates="documents", description="이 문서가 속한 Document_folder 객체에 접근 가능")
    chunks: "List[Chunk]" = relationship("Chunk", back_populates="document", cascade="all, delete-orphan", description="이 문서에 속한 모든 Chunk 객체에 접근 가능")






class Chunk(Base):
    __tablename__ = "chunk"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, description="청크ID")
    doc_id = Column(Integer, ForeignKey(Document.doc_id), nullable=False, description="어떤 문서인지")
    doc_folder_id = Column(Integer, ForeignKey(Document_folder.doc_folder_id), nullable=False, description="어떤 카테고리인지")
    company_id = Column(Integer, ForeignKey("Company.company_id"), description="어떤 회사인지")
    chunk_index = Column(Integer, nullable=False, default=0, description="몇번째 청크인지, 기본값 0")
    embedding = Column(Vector, nullable=True, description="임베딩 벡터")
    metadata_ = Column("metadata", JSONB, nullable=True, description="청크의 메타데이터 저장")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), description="생성일자")

    document: "Document" = relationship("Document", back_populates="chunks", description="이 청크가 속한 Document 객체에 접근 가능")