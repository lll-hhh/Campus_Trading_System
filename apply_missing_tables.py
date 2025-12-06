import sys
import os
from pathlib import Path
from sqlalchemy import text

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from apps.core.database import DatabaseManager

def apply_sql():
    print("🚀 Applying missing tables to MySQL...")
    
    db_manager = DatabaseManager()
    engine = db_manager._engines["mysql"]
    
    sql_path = Path("backend/sql/add_missing_tables_mysql.sql")
    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_path}")
        return

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split by ; but be careful about comments and strings.
    # For this specific file, simple split should work as it contains standard CREATE TABLEs.
    statements = sql_content.split(";")
    
    with engine.connect() as conn:
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            
            try:
                conn.execute(text(statement))
                print(f"✅ Executed: {statement[:50]}...")
            except Exception as e:
                print(f"⚠️ Error executing statement: {e}")
                # Continue even if error (e.g. table already exists)
        
        conn.commit()
    
    print("🎉 SQL application complete.")

if __name__ == "__main__":
    apply_sql()
