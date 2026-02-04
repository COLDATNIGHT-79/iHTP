import asyncio
from app.database import engine, Base
from app.models import Post, Like  # Import models to register them with Base

async def init_models():
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_models())
