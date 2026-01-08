from sqlalchemy import create_engine, text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./bigralph.db"

def migrate_db():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        logger.info("Starting database migration...")
        
        # List of columns to add
        columns = [
            ("first_name", "VARCHAR NOT NULL DEFAULT 'User'"),
            ("last_name", "VARCHAR NOT NULL DEFAULT 'Name'"),
            ("picture", "VARCHAR"),
            ("balance", "INTEGER DEFAULT 0"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_def in columns:
            try:
                # SQLite supports ADD COLUMN
                logger.info(f"Adding column {col_name}...")
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                logger.info(f"Successfully added {col_name}")
            except Exception as e:
                # If column likely exists or other error, log it
                logger.warning(f"Could not add column {col_name}: {e}")
                
        logger.info("Migration completed.")

if __name__ == "__main__":
    migrate_db()
