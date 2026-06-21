import os
import ssl
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, Boolean
from datetime import datetime
from dotenv import load_dotenv

import urllib.parse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+asyncmy://campususer:CampusPrint2025!@localhost:3306/campusprint")

# Ensure the asynchronous driver is used
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+asyncmy://", 1)

# Clean query parameters that the asyncmy driver doesn't accept
if "?" in DATABASE_URL:
    parsed = urllib.parse.urlparse(DATABASE_URL)
    query_params = urllib.parse.parse_qs(parsed.query)
    query_params.pop("ssl-mode", None)
    query_params.pop("ssl_mode", None)
    new_query = urllib.parse.urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)
    DATABASE_URL = urllib.parse.urlunparse(parsed)

connect_args = {}

# Use SSL/TLS if a CA certificate exists and we are not connecting to a local instance
ca_path = Path(__file__).parent / "ca.pem"
is_local = "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL

if ca_path.exists() and not is_local:
    ssl_context = ssl.create_default_context(cafile=str(ca_path))
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ssl_context
    print("SSL connection configured using ca.pem")

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# ✅ This must come before any class that inherits from it
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    username = mapped_column(String(100), unique=True, index=True)
    password_hash = mapped_column(String(255))
    full_name = mapped_column(String(200), nullable=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    is_admin = mapped_column(Boolean, default=False)  # new admin flag

class Order(Base):
    __tablename__ = "orders"
    id = mapped_column(String(36), primary_key=True)
    username = mapped_column(String(100), index=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    status = mapped_column(String(50), default="received")
    student_name = mapped_column(String(200))
    year = mapped_column(String(50))
    branch = mapped_column(String(100))
    section = mapped_column(String(50), nullable=True)
    roll_number = mapped_column(String(100))
    order_description = mapped_column(Text, nullable=True)
    total_pages = mapped_column(Integer)
    copies = mapped_column(Integer)
    print_type = mapped_column(String(50))
    binding = mapped_column(String(50))
    payment_method = mapped_column(String(50))
    file_paths = mapped_column(Text, nullable=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session