"""Set default values for chunk_ids and weight columns

Revision ID: 67bb9d002b95
Revises: ef0aa421cbc6
Create Date: 2025-07-29 13:36:00.889088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67bb9d002b95'
down_revision: Union[str, Sequence[str], None] = 'ef0aa421cbc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 기존 NULL 값들을 기본값으로 업데이트
    op.execute("UPDATE chat SET chunk_ids = '[]'::jsonb WHERE chunk_ids IS NULL")
    op.execute("UPDATE chunk SET weight = 1.0 WHERE weight IS NULL")
    
    # 기본값 설정하고 NOT NULL 제약 조건 추가
    op.alter_column('chat', 'chunk_ids',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               server_default=sa.text("'[]'::jsonb"),
               nullable=False)
    op.alter_column('chunk', 'weight',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               server_default=sa.text("1.0"),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 기본값 제거하고 nullable=True로 되돌리기
    op.alter_column('chunk', 'weight',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               server_default=None,
               nullable=True)
    op.alter_column('chat', 'chunk_ids',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               server_default=None,
               nullable=True)
