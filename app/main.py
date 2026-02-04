from fastapi import FastAPI, Request, Depends, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, or_, func
from uuid import UUID
from datetime import datetime, timedelta
from .database import get_db
from .middleware import AuthMiddleware
from .models import Post, Like
from .admin_auth import (
    verify_password, create_access_token, get_admin_from_cookie, require_admin
)

app = FastAPI()

# Add Middleware
app.add_middleware(AuthMiddleware)

# Mount static files
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ==================== PUBLIC ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    """Home page - random posts in grid"""
    result = await db.execute(
        select(Post).where(Post.status == "active")
        .order_by(func.random()).limit(50)
    )
    posts = result.scalars().all()
    
    try:
        await db.execute(text("SELECT 1"))
        db_status = "Connected 🟢"
    except:
        db_status = "Failed 🔴"

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "db_status": db_status,
        "user_hash": request.state.user_hash[:8] + "...",
        "posts": posts,
        "active_page": "home"
    })

@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Leaderboard page - top liked posts from this week"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(Post)
        .where(Post.created_at >= seven_days_ago)
        .where(Post.status == "active")
        .order_by(Post.like_count.desc())
        .limit(50)
    )
    posts = result.scalars().all()
    
    try:
        await db.execute(text("SELECT 1"))
        db_status = "Connected 🟢"
    except:
        db_status = "Failed 🔴"

    return templates.TemplateResponse("leaderboard.html", {
        "request": request, 
        "db_status": db_status,
        "user_hash": request.state.user_hash[:8] + "...",
        "posts": posts,
        "active_page": "leaderboard"
    })

@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """Create listing page"""
    try:
        db_status = "Connected 🟢"
    except:
        db_status = "Failed 🔴"
        
    return templates.TemplateResponse("create.html", {
        "request": request, 
        "db_status": db_status,
        "user_hash": request.state.user_hash[:8] + "...",
        "active_page": "create"
    })

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def view_post(request: Request, post_id: UUID, db: AsyncSession = Depends(get_db)):
    """Individual post page with SEO metadata"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user_hash = request.state.user_hash
    liked_result = await db.execute(select(Like.post_id).where(Like.client_hash == user_hash))
    liked_post_ids = {str(row[0]) for row in liked_result.fetchall()}
    
    try:
        await db.execute(text("SELECT 1"))
        db_status = "Connected 🟢"
    except:
        db_status = "Failed 🔴"
    
    return templates.TemplateResponse("post.html", {
        "request": request,
        "post": post,
        "db_status": db_status,
        "user_hash": user_hash[:8] + "...",
        "liked_post_ids": liked_post_ids
    })

@app.get("/search", response_class=HTMLResponse)
async def search_posts(request: Request, q: str = Query(""), db: AsyncSession = Depends(get_db)):
    query = q.strip()
    if not query:
        return HTMLResponse("")
    
    search_pattern = f"%{query}%"
    result = await db.execute(
        select(Post).where(
            or_(
                Post.title.ilike(search_pattern),
                Post.description.ilike(search_pattern),
                Post.reason.ilike(search_pattern),
                Post.tags.any(query.lower())
            )
        ).order_by(Post.like_count.desc()).limit(20)
    )
    posts = result.scalars().all()
    
    # Return cards for search results
    return templates.TemplateResponse("components/search_grid.html", {
        "request": request, "posts": posts, "query": query
    })

@app.post("/posts", response_class=HTMLResponse)
async def create_post(
    request: Request, 
    image_url: str = Form(""),
    title: str = Form(...),
    description: str = Form(""), 
    reason: str = Form(""), 
    tag1: str = Form(""),
    tag2: str = Form(""),
    nationality: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    # Build tags list from dropdowns
    tag_list = [t.strip().lower() for t in [tag1, tag2] if t.strip()]
    
    # Store the URL - resolution happens at display time via proxy
    new_post = Post(
        image_url=image_url.strip() if image_url else None,
        title=title[:50],
        description=description[:180] if description else None,
        reason=reason[:250] if reason else None,
        tags=tag_list,
        nationality=nationality if nationality else None,
        author_hash=request.state.user_hash
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    # Redirect to home after creating
    return RedirectResponse(url="/", status_code=303)

@app.post("/posts/{post_id}/like", response_class=HTMLResponse)
async def like_post(request: Request, post_id: UUID, db: AsyncSession = Depends(get_db)):
    user_hash = request.state.user_hash
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.status == "blocked":
        raise HTTPException(status_code=403, detail="Cannot like blocked posts")
    
    existing = await db.execute(
        select(Like).where(Like.post_id == post_id, Like.client_hash == user_hash)
    )
    
    if existing.scalar_one_or_none():
        await db.execute(
            text("DELETE FROM likes WHERE post_id = :post_id AND client_hash = :client_hash"),
            {"post_id": post_id, "client_hash": user_hash}
        )
        post.like_count = max(0, post.like_count - 1)
        is_liked = False
    else:
        db.add(Like(post_id=post_id, client_hash=user_hash))
        post.like_count += 1
        is_liked = True
    
    await db.commit()
    await db.refresh(post)
    return templates.TemplateResponse("components/like_button.html", {
        "request": request, "post": post, "is_liked": is_liked
    })

# ==================== ADMIN ROUTES ====================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    if get_admin_from_cookie(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, password: str = Form(...)):
    if verify_password(password):
        token = create_access_token({"admin": True})
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="admin_token", value=token, httponly=True,
            secure=False, samesite="lax", max_age=60*60*24
        )
        return response
    return templates.TemplateResponse("admin/login.html", {
        "request": request, "error": "Invalid password"
    })

@app.post("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("admin_token")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_admin_from_cookie(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()
    
    try:
        await db.execute(text("SELECT 1"))
        db_status = "Connected 🟢"
    except:
        db_status = "Failed 🔴"
    
    return templates.TemplateResponse("admin/panel.html", {
        "request": request, "posts": posts, "db_status": db_status,
        "user_hash": "ADMIN"
    })

@app.post("/admin/posts/{post_id}/block", response_class=HTMLResponse)
async def block_post(
    request: Request, post_id: UUID, reason: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if not get_admin_from_cookie(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = "blocked"
    post.moderation_reason = reason
    await db.commit()
    await db.refresh(post)
    
    return templates.TemplateResponse("admin/post_row.html", {"request": request, "post": post})

@app.post("/admin/posts/{post_id}/unblock", response_class=HTMLResponse)
async def unblock_post(request: Request, post_id: UUID, db: AsyncSession = Depends(get_db)):
    if not get_admin_from_cookie(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = "active"
    post.moderation_reason = None
    await db.commit()
    await db.refresh(post)
    
    return templates.TemplateResponse("admin/post_row.html", {"request": request, "post": post})
