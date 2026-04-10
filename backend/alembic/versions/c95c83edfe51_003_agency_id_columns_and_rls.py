"""003_agency_id_columns_and_rls

Revision ID: c95c83edfe51
Revises: aa61305c4f97
Create Date: 2026-04-10 09:42:01.835048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c95c83edfe51'
down_revision: Union[str, Sequence[str], None] = 'aa61305c4f97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 0-E + 0-F:
    1. 기존 테이블에 agency_id 컬럼 추가 (nullable, 기존 데이터 호��)
    2. 기존 데이터에 agency_id=1 (기본 에이전시) 설정
    3. RLS 정책 설정 (agency_id 기반 테넌트 격리)
    """
    # --- 1. agency_id 컬럼 추가 ---
    tenant_tables = ['clients', 'campaigns', 'content_schedule', 'ab_tests', 'resource_library']
    for table in tenant_tables:
        op.add_column(table, sa.Column('agency_id', sa.Integer(), nullable=True))
        op.create_index(f'ix_{table}_agency_id', table, ['agency_id'])

    # agency_members에 FK 인덱스
    op.create_index('ix_agency_members_agency_id', 'agency_members', ['agency_id'])

    # --- 2. 기본 에이전시 생성 + 기존 데이터 할당 ---
    op.execute("""
        INSERT INTO agencies (name, owner_email, plan)
        VALUES ('Default Agency', 'admin@omnivibe.pro', 'free')
        ON CONFLICT DO NOTHING
    """)
    for table in tenant_tables:
        op.execute(f"""
            UPDATE {table} SET agency_id = 1 WHERE agency_id IS NULL
        """)

    # --- 3. RLS 정책 설정 ---
    # app.current_agency_id 세션 변수로 테넌트 격리
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (agency_id = current_setting('app.current_agency_id', true)::int)
        """)
    # generated_scripts, storyboard_blocks는 content_schedule 통해 간접 격리 (JOIN 기반)
    # 직접 RLS 대신 view 또는 서비스 레이어에서 필터링

    # agencies/agency_members는 RLS 불필요 (superadmin만 접근)

    # --- 4. omnivibe 사용자에게 RLS bypass 권한 (개발용) ---
    # 프로덕션에서는 별도 app_user 생성 후 bypass 제거
    op.execute("ALTER USER omnivibe SET row_security = off")


def downgrade() -> None:
    """Revert RLS + agency_id."""
    tenant_tables = ['clients', 'campaigns', 'content_schedule', 'ab_tests', 'resource_library']

    for table in tenant_tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.drop_index(f'ix_{table}_agency_id', table_name=table)
        op.drop_column(table, 'agency_id')

    op.drop_index('ix_agency_members_agency_id', table_name='agency_members')
