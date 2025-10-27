import sys
import os
from sqlalchemy import create_engine, text

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

# 导入统一的数据库配置
from config.database import DatabaseConfig

# 使用统一配置创建数据库连接
config = DatabaseConfig()
DB_URL = config.get_connection_string()
engine = create_engine(DB_URL, pool_pre_ping=True)

print("[DB] Connecting...", flush=True)
with engine.begin() as conn:
    print("[DB] Connected.", flush=True)

    def column_exists(conn, table, column):
        q = text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
        )
        return conn.execute(q, {"t": table, "c": column}).scalar() > 0

    def index_exists(conn, table, index_name):
        q = text(
            "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :i"
        )
        return conn.execute(q, {"t": table, "i": index_name}).scalar() > 0

    def ensure_table(conn, create_sql, name):
        print(f"[DB] Ensuring table {name}...", flush=True)
        conn.execute(text(create_sql))
        print(f"[DB] Table {name} ensured.", flush=True)

    def safe_add_column(conn, table, column, ddl):
        if not column_exists(conn, table, column):
            print(f"[DB] Adding column {table}.{column}...", flush=True)
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
            print(f"[DB] Added column {table}.{column}.", flush=True)
        else:
            print(f"[DB] Column {table}.{column} already exists.", flush=True)

    def safe_create_unique(conn, table, index_name, cols):
        if not index_exists(conn, table, index_name):
            print(f"[DB] Creating unique index {index_name} on {table}...", flush=True)
            conn.execute(text(f"ALTER TABLE {table} ADD UNIQUE KEY {index_name} ({cols})"))
            print(f"[DB] Unique index {index_name} created.", flush=True)
        else:
            print(f"[DB] Unique index {index_name} already exists.", flush=True)

    # --- Extend financial_reports ---
    t = "financial_reports"
    safe_add_column(conn, t, "report_year", "report_year INT NULL")
    safe_add_column(conn, t, "report_type", "report_type ENUM('annual','semi_annual','quarterly') NULL")
    safe_add_column(conn, t, "report_title", "report_title VARCHAR(200) NULL")
    safe_add_column(conn, t, "pdf_url", "pdf_url VARCHAR(500) NULL")
    safe_add_column(conn, t, "local_path", "local_path VARCHAR(500) NULL")
    safe_add_column(conn, t, "file_size", "file_size BIGINT NULL")
    safe_add_column(conn, t, "crawl_status", "crawl_status ENUM('pending','success','failed') NULL DEFAULT 'pending'")
    safe_add_column(conn, t, "crawled_at", "crawled_at DATETIME NULL")
    safe_add_column(conn, t, "created_at", "created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP")
    safe_create_unique(conn, t, "unique_report", "stock_code, report_year, report_type")

    # --- Create new tables ---
    ensure_table(conn, """
    CREATE TABLE IF NOT EXISTS companies (
      id INT AUTO_INCREMENT PRIMARY KEY,
      stock_code VARCHAR(10) NOT NULL UNIQUE,
      company_name VARCHAR(100) NOT NULL,
      industry VARCHAR(50) NULL,
      listing_date DATE NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, "companies")

    ensure_table(conn, """
    CREATE TABLE IF NOT EXISTS report_contents (
      id INT AUTO_INCREMENT PRIMARY KEY,
      report_id INT NOT NULL,
      content_type ENUM('overview','balance_sheet','income_statement','cash_flow','notes') NOT NULL,
      extracted_text LONGTEXT NULL,
      page_count INT NULL,
      extraction_method VARCHAR(50) NULL,
      confidence_score FLOAT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT fk_report_contents_report FOREIGN KEY (report_id) REFERENCES financial_reports(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, "report_contents")

    ensure_table(conn, """
    CREATE TABLE IF NOT EXISTS financial_metrics (
      id INT AUTO_INCREMENT PRIMARY KEY,
      report_id INT NOT NULL,
      metric_name VARCHAR(50) NOT NULL,
      metric_value DOUBLE NULL,
      metric_unit VARCHAR(20) NULL,
      calculation_method VARCHAR(100) NULL,
      period_type ENUM('Q1','Q2','Q3','Q4','HY','FY') NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT fk_financial_metrics_report FOREIGN KEY (report_id) REFERENCES financial_reports(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, "financial_metrics")

    ensure_table(conn, """
    CREATE TABLE IF NOT EXISTS ai_analyses (
      id INT AUTO_INCREMENT PRIMARY KEY,
      report_id INT NOT NULL,
      analysis_type ENUM('basic','deep','comparison','investment') NOT NULL,
      model_used VARCHAR(50) NULL,
      analysis_result JSON NULL,
      confidence_level ENUM('low','medium','high') NULL,
      processing_time INT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT fk_ai_analyses_report FOREIGN KEY (report_id) REFERENCES financial_reports(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, "ai_analyses")

    ensure_table(conn, """
    CREATE TABLE IF NOT EXISTS industry_comparisons (
      id INT AUTO_INCREMENT PRIMARY KEY,
      stock_code VARCHAR(10) NOT NULL,
      comparison_date DATE NOT NULL,
      industry_avg_metrics JSON NULL,
      ranking_position INT NULL,
      percentile_score DOUBLE NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT fk_industry_companies_stock FOREIGN KEY (stock_code) REFERENCES companies(stock_code) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """, "industry_comparisons")

print("[DB] Migration completed.", flush=True)
