import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

# Loyihaning ildiz papkasidagi (root) .env faylini topish va yuklash
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
print("=============================================================")
print(f"--- .env fayl yo'li: {env_path} | Mavjudmi: {env_path.exists()} ---")
load_dotenv(dotenv_path=env_path)

# Default qiymatsiz majburiy o'qish (agar topilmasa xato beradi)
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = os.environ["POSTGRES_PORT"]

print("==============================================================")

print(f"POSTGRES_USER: {POSTGRES_USER}")
print(f"POSTGRES_PASSWORD: {POSTGRES_PASSWORD}")
print(f"POSTGRES_DB: {POSTGRES_DB}")
print(f"POSTGRES_HOST: {POSTGRES_HOST}")
print(f"POSTGRES_PORT: {POSTGRES_PORT}")

ASYNC_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
SYNC_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Async Engine
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync Engine
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()