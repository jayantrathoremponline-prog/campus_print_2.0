import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import uuid
import json
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserCreate, UserLogin, Token, OrderStatusUpdate
from auth import create_access_token, verify_token, get_password_hash, verify_password
from database import get_db, init_db, User, Order
from storage import save_uploaded_file

app = FastAPI(title="CampusPrint Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads folder to serve files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Create tables on startup
@app.on_event("startup")
async def startup():
    await init_db()

# Dependency to get current user from JWT token
def get_current_user(token: str = Depends(verify_token)):
    return token

# ------------------------------
# Authentication endpoints
# ------------------------------
@app.post("/api/signup", response_model=Token)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed, full_name=user.full_name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------------------
# User info endpoint
# ------------------------------
@app.get("/api/me")
async def get_current_user_info(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == current_user))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "full_name": user.full_name,
        "is_admin": user.is_admin
    }

# ------------------------------
# Admin endpoints
# ------------------------------
async def get_current_admin_user(current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == current_user))
    user = result.scalar_one_or_none()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@app.get("/api/admin/orders")
async def admin_list_orders(admin_user: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    orders = result.scalars().all()
    orders_list = []
    for order in orders:
        # Parse file_paths JSON string
        file_paths_list = json.loads(order.file_paths) if order.file_paths else []
        
        # Generate clean URLs
        file_urls = []
        for path in file_paths_list:
            # Remove 'uploads/' prefix if present, and fix Windows backslashes
            clean_path = path.replace('uploads/', '').replace('uploads\\', '').replace('\\', '/')
            file_urls.append(f"/uploads/{clean_path}")

        orders_list.append({
            "id": order.id,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "student_name": order.student_name,
            "username": order.username,
            "year": order.year,
            "branch": order.branch,
            "roll_number": order.roll_number,
            "total_pages": order.total_pages,
            "copies": order.copies,
            "print_type": order.print_type,
            "binding": order.binding,
            "payment_method": order.payment_method,
            "file_paths": order.file_paths,
            "file_urls": file_urls
        })
    return {"orders": orders_list}
@app.put("/api/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status_update.status
    await db.commit()
    await db.refresh(order)
    return {"message": "Order status updated", "order_id": order_id, "new_status": order.status}

# ------------------------------
# Student order endpoints
# ------------------------------
@app.post("/api/orders")
async def place_order(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    student_name: str = Form(...),
    year: str = Form(...),
    branch: str = Form(...),
    section: Optional[str] = Form(None),
    roll_number: str = Form(...),
    order_description: Optional[str] = Form(None),
    total_pages: int = Form(...),
    copies: int = Form(...),
    print_type: str = Form(...),
    binding: str = Form(...),
    payment_method: str = Form(...),
    files: List[UploadFile] = File(...)
):
    saved_files = []
    for f in files:
        file_path = await save_uploaded_file(f, current_user)
        saved_files.append(file_path)
    
    order_id = str(uuid.uuid4())
    new_order = Order(
        id=order_id,
        username=current_user,
        student_name=student_name,
        year=year,
        branch=branch,
        section=section,
        roll_number=roll_number,
        order_description=order_description,
        total_pages=total_pages,
        copies=copies,
        print_type=print_type,
        binding=binding,
        payment_method=payment_method,
        file_paths=json.dumps(saved_files)
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    return {"status": "success", "order_id": order_id}

@app.get("/api/orders")
async def list_orders(current_user: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.username == current_user))
    orders = result.scalars().all()
    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "student_name": order.student_name,
            "total_pages": order.total_pages,
            "copies": order.copies,
            "print_type": order.print_type,
            "binding": order.binding,
            "payment_method": order.payment_method,
            "file_paths": order.file_paths
        })
    return {"orders": orders_list}

@app.delete("/api/admin/orders/{order_id}")
async def delete_order(
    order_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an order (admin only)."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.delete(order)
    await db.commit()
    return {"message": "Order deleted successfully"}
    
@app.get("/")
def root():
    return {"message": "CampusPrint API is running"}