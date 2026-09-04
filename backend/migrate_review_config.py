"""
添加 review_config 字段到 contracts 表

用于存储审查立场配置（甲乙方立场、合同金额、风险偏好）
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "legal_saas.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(contracts)")
    columns = [col[1] for col in cursor.fetchall()]

    if "review_config" not in columns:
        cursor.execute("ALTER TABLE contracts ADD COLUMN review_config JSON")
        conn.commit()
        print("[OK] review_config field added")
    else:
        print("[OK] review_config field already exists")

    conn.close()

if __name__ == "__main__":
    migrate()
