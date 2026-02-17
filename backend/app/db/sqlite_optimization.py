"""
SQLite3 프로덕션 최적화

WAL 모드, PRAGMA 설정, 인덱스, 백업 자동화
"""
import sqlite3
import os
import logging
import shutil
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteOptimizer:
    """
    SQLite3 데이터베이스 최적화 관리자
    """

    def __init__(self, db_path: str = "omni_db.sqlite"):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def optimize_for_production(self):
        """
        프로덕션 환경에 최적화된 PRAGMA 설정 적용
        """
        logger.info(f"Optimizing SQLite database: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. WAL (Write-Ahead Logging) 모드 활성화
            # - 읽기와 쓰기 동시 수행 가능
            # - 성능 향상 30-50%
            cursor.execute("PRAGMA journal_mode=WAL")
            logger.info("✓ WAL mode enabled")

            # 2. Synchronous 모드 (NORMAL)
            # - FULL: 가장 안전하지만 느림
            # - NORMAL: 대부분의 경우 안전하며 빠름
            # - OFF: 가장 빠르지만 위험 (권장 안 함)
            cursor.execute("PRAGMA synchronous=NORMAL")
            logger.info("✓ Synchronous mode set to NORMAL")

            # 3. Cache Size (64MB)
            # - 기본값: 2MB (-2000 pages)
            # - 권장값: 64MB (-64000 pages)
            cursor.execute("PRAGMA cache_size=-64000")
            logger.info("✓ Cache size set to 64MB")

            # 4. Temp Store (MEMORY)
            # - 임시 테이블을 메모리에 저장
            cursor.execute("PRAGMA temp_store=MEMORY")
            logger.info("✓ Temp store set to MEMORY")

            # 5. Memory-Mapped I/O (256MB)
            # - mmap 사용으로 읽기 성능 향상
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
            logger.info("✓ Memory-mapped I/O enabled (256MB)")

            # 6. Auto Vacuum (INCREMENTAL)
            # - 공간 회수를 점진적으로 수행
            cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")
            logger.info("✓ Auto vacuum set to INCREMENTAL")

            # 7. Page Size (4096 bytes)
            # - 기본값: 4096 (대부분의 시스템에 최적)
            cursor.execute("PRAGMA page_size=4096")
            logger.info("✓ Page size set to 4096 bytes")

            # 8. Busy Timeout (5초)
            # - 데이터베이스 잠금 시 대기 시간
            cursor.execute("PRAGMA busy_timeout=5000")
            logger.info("✓ Busy timeout set to 5 seconds")

            conn.commit()
            logger.info("🚀 SQLite optimization completed successfully")

        except Exception as e:
            logger.error(f"Failed to optimize SQLite: {e}")
            raise
        finally:
            conn.close()

    def create_indexes(self):
        """
        자주 조회되는 컬럼에 인덱스 생성
        """
        logger.info("Creating database indexes...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        indexes = [
            # Campaigns
            "CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_platform ON campaigns(platform)",

            # Contents
            "CREATE INDEX IF NOT EXISTS idx_contents_campaign ON contents(campaign_id)",
            "CREATE INDEX IF NOT EXISTS idx_contents_status ON contents(status)",
            "CREATE INDEX IF NOT EXISTS idx_contents_published ON contents(published_at)",

            # Script Blocks
            "CREATE INDEX IF NOT EXISTS idx_script_blocks_content ON script_blocks(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_script_blocks_sequence ON script_blocks(sequence)",

            # Audio Generations
            "CREATE INDEX IF NOT EXISTS idx_audio_generations_task ON audio_generations(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_audio_generations_content ON audio_generations(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_audio_generations_status ON audio_generations(status)",

            # Performance Metrics
            "CREATE INDEX IF NOT EXISTS idx_performance_content ON performance_metrics(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_performance_platform ON performance_metrics(platform)",
            "CREATE INDEX IF NOT EXISTS idx_performance_recorded ON performance_metrics(recorded_at)",

            # Audit Logs
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)",
        ]

        try:
            for index_sql in indexes:
                cursor.execute(index_sql)
                logger.info(f"✓ {index_sql.split('idx_')[1].split(' ')[0]}")

            conn.commit()
            logger.info("🚀 All indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
        finally:
            conn.close()

    def vacuum(self):
        """
        VACUUM 실행 (데이터베이스 압축 및 최적화)

        주의: VACUUM은 데이터베이스 전체를 재작성하므로 시간이 걸립니다.
        권장: 주기적으로 실행 (월 1회)
        """
        logger.info("Running VACUUM (this may take a while)...")

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("VACUUM")
            logger.info("✓ VACUUM completed")
        except Exception as e:
            logger.error(f"VACUUM failed: {e}")
            raise
        finally:
            conn.close()

    def analyze(self):
        """
        ANALYZE 실행 (쿼리 최적화를 위한 통계 수집)

        권장: 인덱스 생성 후, 데이터 대량 변경 후
        """
        logger.info("Running ANALYZE...")

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("ANALYZE")
            logger.info("✓ ANALYZE completed")
        except Exception as e:
            logger.error(f"ANALYZE failed: {e}")
            raise
        finally:
            conn.close()

    def backup(self, backup_name: Optional[str] = None) -> str:
        """
        데이터베이스 백업

        Args:
            backup_name: 백업 파일명 (지정하지 않으면 타임스탬프)

        Returns:
            백업 파일 경로
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"omni_db_backup_{timestamp}.sqlite"

        backup_path = self.backup_dir / backup_name

        logger.info(f"Creating backup: {backup_path}")

        try:
            # 파일 복사 (WAL 모드에서도 안전)
            shutil.copy2(self.db_path, backup_path)

            # WAL 파일도 백업 (존재하는 경우)
            wal_path = f"{self.db_path}-wal"
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, f"{backup_path}-wal")

            # SHM 파일도 백업 (존재하는 경우)
            shm_path = f"{self.db_path}-shm"
            if os.path.exists(shm_path):
                shutil.copy2(shm_path, f"{backup_path}-shm")

            logger.info(f"✓ Backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise

    def cleanup_old_backups(self, keep_count: int = 7):
        """
        오래된 백업 파일 삭제

        Args:
            keep_count: 유지할 백업 개수 (기본 7개)
        """
        logger.info(f"Cleaning up old backups (keeping {keep_count})...")

        backups = sorted(
            self.backup_dir.glob("omni_db_backup_*.sqlite"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        deleted_count = 0
        for backup in backups[keep_count:]:
            try:
                backup.unlink()
                # WAL, SHM 파일도 삭제
                wal_file = Path(f"{backup}-wal")
                shm_file = Path(f"{backup}-shm")
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()

                deleted_count += 1
                logger.info(f"✓ Deleted old backup: {backup.name}")
            except Exception as e:
                logger.error(f"Failed to delete {backup}: {e}")

        logger.info(f"✓ Cleaned up {deleted_count} old backups")

    def get_database_info(self) -> dict:
        """
        데이터베이스 정보 조회

        Returns:
            데이터베이스 설정 및 통계
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        info = {}

        try:
            # PRAGMA 설정 조회
            pragmas = [
                "journal_mode",
                "synchronous",
                "cache_size",
                "temp_store",
                "mmap_size",
                "auto_vacuum",
                "page_size",
                "page_count",
                "freelist_count"
            ]

            for pragma in pragmas:
                cursor.execute(f"PRAGMA {pragma}")
                value = cursor.fetchone()[0]
                info[pragma] = value

            # 데이터베이스 크기
            file_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            info["file_size_mb"] = round(file_size_mb, 2)

            # 테이블 개수
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            info["table_count"] = cursor.fetchone()[0]

            # 인덱스 개수
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            info["index_count"] = cursor.fetchone()[0]

            return info

        finally:
            conn.close()


def optimize_database(db_path: str = "omni_db.sqlite"):
    """
    데이터베이스 전체 최적화 (프로덕션 배포 시 실행)

    Args:
        db_path: 데이터베이스 파일 경로
    """
    optimizer = SQLiteOptimizer(db_path)

    # 1. 백업 생성
    optimizer.backup()

    # 2. PRAGMA 최적화
    optimizer.optimize_for_production()

    # 3. 인덱스 생성
    optimizer.create_indexes()

    # 4. 통계 수집
    optimizer.analyze()

    # 5. VACUUM (선택사항 - 시간 소요)
    # optimizer.vacuum()

    # 6. 정보 출력
    info = optimizer.get_database_info()
    logger.info(f"Database Info: {info}")

    # 7. 오래된 백업 정리
    optimizer.cleanup_old_backups(keep_count=7)

    logger.info("✅ Database optimization completed!")


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # 최적화 실행
    optimize_database()
