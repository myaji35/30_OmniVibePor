"""004_clients_brand_extraction_columns

Revision ID: 3760ce6bc590
Revises: c95c83edfe51
Create Date: 2026-04-10 09:56:04.049204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3760ce6bc590'
down_revision: Union[str, Sequence[str], None] = 'c95c83edfe51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """ISS-085 Stage 2: clients 테이블에 브랜드 추출 컬럼 추가."""
    op.add_column('clients', sa.Column('website_url', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('tagline', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('auto_extracted_at', sa.DateTime(), nullable=True))
    op.add_column('clients', sa.Column('extract_source', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('extract_raw_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Revert brand extraction columns."""
    for col in ['extract_raw_json', 'extract_source', 'auto_extracted_at',
                'tagline', 'phone', 'address', 'website_url']:
        op.drop_column('clients', col)
