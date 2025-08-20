#!/usr/bin/env python3
"""
Upload Fixed Database Script
Manually uploads the corrected database with processed=1 flags
"""
import shutil
from pathlib import Path

def main():
    # Copy our fixed database to ensure it gets uploaded properly
    source_db = Path("podcast_app_v2.db")
    backup_db = Path("podcast_app_v2_fixed.db")
    
    if source_db.exists():
        shutil.copy2(source_db, backup_db)
        print(f"✅ Created backup of fixed database: {backup_db}")
        print(f"Database size: {source_db.stat().st_size / 1024:.1f} KB")
        
        # Verify the fix is in place
        import sqlite3
        conn = sqlite3.connect(source_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM episodes WHERE processed = 1")
        processed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM episodes")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Database status:")
        print(f"   Total episodes: {total_count}")
        print(f"   Processed episodes: {processed_count}")
        
        if processed_count == total_count:
            print("✅ Database is correctly fixed!")
            return True
        else:
            print(f"❌ Database still has {total_count - processed_count} unprocessed episodes")
            return False
    else:
        print("❌ Database file not found")
        return False

if __name__ == "__main__":
    main()