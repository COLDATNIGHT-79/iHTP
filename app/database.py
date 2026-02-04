import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Handle empty URL gracefully
if not DATABASE_URL:
    print("WARNING: DATABASE_URL not found. Using dummy fallback.")
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

# Parse URL
try:
    db_url = make_url(DATABASE_URL)
except Exception as e:
    print(f"Error parsing database URL: {e}")
    db_url = make_url("postgresql+asyncpg://user:pass@localhost/dbname")

# Switch to asyncpg driver if needed
if db_url.drivername in ('postgresql', 'postgres'):
    db_url = db_url.set(drivername='postgresql+asyncpg')

# Fix for asyncpg: strip 'sslmode' and 'channel_binding' from query params
# and pass 'ssl' in connect_args instead
query_params = dict(db_url.query)
connect_args = {}

# Handle sslmode -> connect_args['ssl']
if 'sslmode' in query_params:
    ssl_val = query_params.pop('sslmode')
    if ssl_val != 'disable':
        connect_args['ssl'] = 'require'

# Handle channel_binding - strip it to avoid "unexpected keyword argument"
if 'channel_binding' in query_params:
    query_params.pop('channel_binding')

# Reconstruct URL without the problematic query params
db_url = db_url.set(query=query_params)

# Create engine
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
