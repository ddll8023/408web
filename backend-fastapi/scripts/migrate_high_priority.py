#!/usr/bin/env python3
"""保留题库数据的高优先级 SQLite 结构迁移。"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


MIGRATION_VERSION = "001_high_priority_security_and_integrity"
DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "web408.db"


def quote(identifier: str) -> str:
    """安全引用固定的 SQLite 标识符。"""
    return '"' + identifier.replace('"', '""') + '"'


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def migration_applied(connection: sqlite3.Connection) -> bool:
    if not table_exists(connection, "schema_migrations"):
        return False
    row = connection.execute(
        "SELECT 1 FROM schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    return row is not None


def create_backup(database_path: Path) -> Path:
    """在迁移前创建不覆盖旧备份的副本。"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = database_path.with_name(
        f"{database_path.stem}.pre_{MIGRATION_VERSION}_{timestamp}{database_path.suffix}.backup"
    )
    shutil.copy2(database_path, backup_path)
    return backup_path


def count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {quote(table_name)}").fetchone()[0])


def assert_no_duplicates(connection: sqlite3.Connection) -> None:
    duplicate_queries = {
        "真题年份题号": """
            SELECT year, question_number FROM exam_question
            WHERE question_number IS NOT NULL
            GROUP BY year, question_number HAVING COUNT(*) > 1
        """,
        "模拟题来源标题题号": """
            SELECT source, title, question_number FROM mock_question
            WHERE title IS NOT NULL AND question_number IS NOT NULL
            GROUP BY source, title, question_number HAVING COUNT(*) > 1
        """,
        "分类名称": """
            SELECT subject_id, name FROM exam_category
            GROUP BY subject_id, name HAVING COUNT(*) > 1
        """,
        "分类编码": """
            SELECT subject_id, code FROM exam_category
            GROUP BY subject_id, code HAVING COUNT(*) > 1
        """,
    }
    for description, query in duplicate_queries.items():
        if connection.execute(query).fetchone() is not None:
            raise RuntimeError(f"迁移中止：检测到重复的{description}，未修改数据库")


def assert_references_are_valid(connection: sqlite3.Connection) -> None:
    checks = {
        "真题科目": """
            SELECT 1 FROM exam_question q LEFT JOIN subject s ON s.id=q.subject_id
            WHERE q.subject_id IS NOT NULL AND s.id IS NULL LIMIT 1
        """,
        "模拟题科目": """
            SELECT 1 FROM mock_question q LEFT JOIN subject s ON s.id=q.subject_id
            WHERE q.subject_id IS NOT NULL AND s.id IS NULL LIMIT 1
        """,
        "章节科目": """
            SELECT 1 FROM chapter c LEFT JOIN subject s ON s.id=c.subject_id
            WHERE s.id IS NULL LIMIT 1
        """,
        "分类科目": """
            SELECT 1 FROM exam_category c LEFT JOIN subject s ON s.id=c.subject_id
            WHERE s.id IS NULL LIMIT 1
        """,
        "章节父节点": """
            SELECT 1 FROM chapter c LEFT JOIN chapter p ON p.id=c.parent_id
            WHERE c.parent_id IS NOT NULL AND p.id IS NULL LIMIT 1
        """,
        "分类父节点": """
            SELECT 1 FROM exam_category c LEFT JOIN exam_category p ON p.id=c.parent_id
            WHERE c.parent_id IS NOT NULL AND p.id IS NULL LIMIT 1
        """,
    }
    for description, query in checks.items():
        if connection.execute(query).fetchone() is not None:
            raise RuntimeError(f"迁移中止：存在无效的{description}引用，未修改数据库")


def get_admin_id(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        "SELECT id FROM user WHERE role='ADMIN' ORDER BY id"
    ).fetchall()
    if len(rows) != 1:
        raise RuntimeError(
            f"迁移中止：期望恰好一个 ADMIN 账号，实际为 {len(rows)} 个，未修改数据库"
        )
    return int(rows[0][0])


def rebuild_table(
    connection: sqlite3.Connection,
    table_name: str,
    definition: str,
    columns: list[str],
) -> None:
    temporary_name = f"{table_name}__migration"
    connection.execute(f"DROP TABLE IF EXISTS {quote(temporary_name)}")
    connection.execute(definition.replace("__TABLE__", quote(temporary_name)))
    column_sql = ", ".join(quote(column) for column in columns)
    connection.execute(
        f"INSERT INTO {quote(temporary_name)} ({column_sql}) "
        f"SELECT {column_sql} FROM {quote(table_name)}"
    )
    connection.execute(f"DROP TABLE {quote(table_name)}")
    connection.execute(
        f"ALTER TABLE {quote(temporary_name)} RENAME TO {quote(table_name)}"
    )


def rebuild_schema(connection: sqlite3.Connection) -> None:
    rebuild_table(
        connection,
        "user",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'USER'
                CHECK (role IN ('ADMIN', 'USER', 'GUEST')),
            enabled INTEGER NOT NULL DEFAULT 1,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL
        )
        """,
        ["id", "username", "password", "email", "role", "enabled", "create_time", "update_time"],
    )
    rebuild_table(
        connection,
        "subject",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            description TEXT,
            order_num INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL
        )
        """,
        ["id", "name", "code", "description", "order_num", "enabled", "create_time", "update_time"],
    )
    rebuild_table(
        connection,
        "chapter",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            parent_id INTEGER,
            name TEXT NOT NULL,
            order_num INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES chapter(id) ON DELETE CASCADE
        )
        """,
        ["id", "create_time", "update_time", "subject_id", "parent_id", "name", "order_num", "enabled"],
    )
    rebuild_table(
        connection,
        "exam_category",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            parent_id INTEGER,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            description TEXT,
            order_num INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES exam_category(id) ON DELETE CASCADE
        )
        """,
        ["id", "create_time", "update_time", "subject_id", "parent_id", "name", "code", "description", "order_num", "enabled"],
    )
    rebuild_table(
        connection,
        "exam_question",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            year INTEGER NOT NULL,
            question_number INTEGER,
            question_type TEXT NOT NULL DEFAULT 'ESSAY'
                CHECK (question_type IN ('CHOICE', 'ESSAY')),
            title TEXT,
            content TEXT NOT NULL,
            options TEXT,
            answer TEXT,
            category TEXT,
            subject_id INTEGER,
            difficulty TEXT
                CHECK (difficulty IS NULL OR difficulty IN ('EASY', 'MEDIUM', 'HARD')),
            author_id INTEGER NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE SET NULL,
            FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE RESTRICT
        )
        """,
        ["id", "create_time", "update_time", "year", "question_number", "question_type", "title", "content", "options", "answer", "category", "subject_id", "difficulty", "author_id"],
    )
    rebuild_table(
        connection,
        "mock_question",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            source TEXT NOT NULL,
            question_number INTEGER,
            question_type TEXT NOT NULL DEFAULT 'ESSAY'
                CHECK (question_type IN ('CHOICE', 'ESSAY')),
            title TEXT,
            content TEXT NOT NULL,
            options TEXT,
            answer TEXT,
            category TEXT,
            subject_id INTEGER,
            difficulty TEXT
                CHECK (difficulty IS NULL OR difficulty IN ('EASY', 'MEDIUM', 'HARD')),
            author_id INTEGER NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subject(id) ON DELETE SET NULL,
            FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE RESTRICT
        )
        """,
        ["id", "create_time", "update_time", "source", "question_number", "question_type", "title", "content", "options", "answer", "category", "subject_id", "difficulty", "author_id"],
    )
    rebuild_table(
        connection,
        "resource_file",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_type TEXT,
            description TEXT,
            download_count INTEGER NOT NULL DEFAULT 0,
            uploader_id INTEGER NOT NULL,
            FOREIGN KEY (uploader_id) REFERENCES user(id) ON DELETE RESTRICT
        )
        """,
        ["id", "create_time", "update_time", "filename", "original_filename", "file_path", "file_size", "file_type", "description", "download_count", "uploader_id"],
    )
    rebuild_table(
        connection,
        "exam_random_stat",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            user_id INTEGER NOT NULL UNIQUE,
            total_attempts INTEGER NOT NULL DEFAULT 0,
            last_attempt_time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
        """,
        ["id", "create_time", "update_time", "user_id", "total_attempts", "last_attempt_time"],
    )
    rebuild_table(
        connection,
        "knowledge_point",
        """
        CREATE TABLE __TABLE__ (
            id INTEGER PRIMARY KEY,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            chapter_id INTEGER,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            view_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (chapter_id) REFERENCES chapter(id) ON DELETE SET NULL,
            FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE RESTRICT
        )
        """,
        ["id", "create_time", "update_time", "title", "category", "chapter_id", "content", "author_id", "view_count"],
    )


def create_indexes(connection: sqlite3.Connection) -> None:
    statements = (
        "CREATE INDEX IF NOT EXISTS idx_chapter_subject_id ON chapter(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_chapter_parent_id ON chapter(parent_id)",
        "CREATE INDEX IF NOT EXISTS idx_exam_category_subject_id ON exam_category(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_exam_category_parent_id ON exam_category(parent_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_category_subject_name ON exam_category(subject_id, name)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_category_subject_code ON exam_category(subject_id, code)",
        "CREATE INDEX IF NOT EXISTS idx_exam_question_subject_id ON exam_question(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_exam_question_author_id ON exam_question(author_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_exam_question_year_number "
        "ON exam_question(year, question_number) WHERE question_number IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_mock_question_subject_id ON mock_question(subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_mock_question_author_id ON mock_question(author_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_mock_question_source_title_number "
        "ON mock_question(source, title, question_number) "
        "WHERE title IS NOT NULL AND question_number IS NOT NULL",
    )
    for statement in statements:
        connection.execute(statement)


def migrate(database_path: Path) -> Path | None:
    if not database_path.is_file():
        raise FileNotFoundError(f"数据库不存在: {database_path}")

    with sqlite3.connect(database_path) as connection:
        if migration_applied(connection):
            return None

        required_tables = {
            "user",
            "subject",
            "chapter",
            "exam_category",
            "exam_question",
            "mock_question",
            "resource_file",
            "exam_random_stat",
            "knowledge_point",
        }
        missing = sorted(table for table in required_tables if not table_exists(connection, table))
        if missing:
            raise RuntimeError(f"迁移中止：缺少数据表 {', '.join(missing)}，未修改数据库")

        admin_id = get_admin_id(connection)
        assert_no_duplicates(connection)
        assert_references_are_valid(connection)

        # 非管理员账号如果仍被统计表引用，无法在不丢失统计记录的情况下合并。
        stat_conflict = connection.execute(
            "SELECT 1 FROM exam_random_stat WHERE user_id <> ? LIMIT 1",
            (admin_id,),
        ).fetchone()
        if stat_conflict is not None:
            raise RuntimeError(
                "迁移中止：存在非管理员随机出题统计，需先确认统计数据合并方式，未修改数据库"
            )

        backup_path = create_backup(database_path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN")
        try:
            # 题库数据保留，但作者归属统一到唯一管理员账号。
            for table, column in (
                ("exam_question", "author_id"),
                ("mock_question", "author_id"),
                ("resource_file", "uploader_id"),
                ("knowledge_point", "author_id"),
            ):
                connection.execute(
                    f"UPDATE {quote(table)} SET {quote(column)}=?",
                    (admin_id,),
                )
            connection.execute("DELETE FROM user WHERE id <> ?", (admin_id,))

            rebuild_schema(connection)
            create_indexes(connection)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (MIGRATION_VERSION, datetime.now(timezone.utc).isoformat()),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.execute("PRAGMA foreign_keys=ON")

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"迁移后外键检查失败: {violations}")

        return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移 408Web SQLite 数据库并保留题库数据")
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"数据库路径（默认：{DEFAULT_DATABASE}）",
    )
    args = parser.parse_args()
    backup_path = migrate(args.database.resolve())
    if backup_path is None:
        print(f"迁移已执行，无需重复操作: {args.database.resolve()}")
    else:
        print(f"迁移完成: {args.database.resolve()}")
        print(f"迁移前备份: {backup_path}")


if __name__ == "__main__":
    main()
