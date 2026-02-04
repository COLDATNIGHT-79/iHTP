import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Running database migration...")
        
        # Add image_data column for base64 storage
        try:
            await conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS image_data TEXT"))
            print("✓ image_data column added")
        except Exception as e:
            print(f"! image_data: {e}")
        
        # Fix status column
        try:
            await conn.execute(text("""
                ALTER TABLE posts 
                ALTER COLUMN status TYPE VARCHAR(20) 
                USING status::text
            """))
            print("✓ status column converted to varchar")
        except Exception as e:
            print(f"! status conversion: {e}")
        
        # Set default for status
        try:
            await conn.execute(text("ALTER TABLE posts ALTER COLUMN status SET DEFAULT 'active'"))
            print("✓ status default set")
        except Exception as e:
            print(f"! status default: {e}")
        
        # Add other missing columns
        columns = [
            ("image_url", "TEXT"),
            ("title", "VARCHAR(50)"),
            ("description", "VARCHAR(180)"),
            ("reason", "VARCHAR(250)"),
            ("nationality", "VARCHAR(5)")
        ]
        
        for col_name, col_type in columns:
            try:
                await conn.execute(text(f"ALTER TABLE posts ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                print(f"✓ {col_name}")
            except Exception as e:
                print(f"! {col_name}: {e}")
        
        # Migrate old content to title
        await conn.execute(text("UPDATE posts SET title = SUBSTRING(content, 1, 50) WHERE title IS NULL AND content IS NOT NULL"))
        
        # Update NULL status to active
        await conn.execute(text("UPDATE posts SET status = 'active' WHERE status IS NULL"))
        
        print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
