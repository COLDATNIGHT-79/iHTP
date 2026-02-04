import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found. Database connection will fail.")
    DATABASE_URL = "postgresql+asyncpg://localhost/test"

# Parse URL
db_url = make_url(DATABASE_URL)

# Switch to asyncpg driver
if db_url.drivername == 'postgresql':
    db_url = db_url.set(drivername='postgresql+asyncpg')

# Fix for "unexpected keyword argument 'sslmode'" error with asyncpg
# asyncpg uses 'ssl' parameter in connect_args, not 'sslmode' in query params
connect_args = {}
if 'sslmode' in db_url.query:
    # If sslmode is present, we remove it from query and set ssl context if needed
    # For Neon/Render, simple SSL is usually required
    ssl_mode = db_url.query['sslmode']
    
    # Remove sslmode from query parameters to avoid the TypeError
    query = dict(db_url.query)
    del query['sslmode']
    db_url = db_url.set(query=query)
    
    # Render/Neon need SSL, so we default to True which implies sslmode='require'
    if ssl_mode != 'disable':
        connect_args["ssl"] = True

engine = create_async_engine(
    db_url, 
    echo=False,
    connect_args=connect_args
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
