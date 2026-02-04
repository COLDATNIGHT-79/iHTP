# Anonymous Identity System Design

## Philosophy
**"Persistent but Private"**
We need to know *it's the same person* to prevent double-likes and ban bad actors, but we don't want to know *who they are* or track them elsewhere.

---

## 1. The "Identity Token" (Cookie)
The user holds a single secret token in their browser.
*   **Name**: `anon_id`
*   **Value**: `UUID4` (Random 128-bit string).
*   **Attributes**:
    *   `HttpOnly`: Cannot be accessed by JavaScript (prevents XSS theft).
    *   `Secure`: Only sent over HTTPS.
    *   `SameSite=Lax`: Prevents CSRF.
    *   `Max-Age`: **10 Years** (We want this to be permanent).

### Lifecycle
1.  **First Visit**: Middleware checks for `anon_id` cookie.
2.  **Creation**: If missing, server generates `uuid.uuid4()`, signs it (to prevent tampering), and sets the cookie.
3.  **Rotation**: NONE. The ID remains constant to support long-term "Likes" and "Bans".

---

## 2. Server-Side Hashing (Privacy Layer)
We **NEVER** store the raw `anon_id` in the database. If the DB leaks, we don't want to be able to impersonate users.

### The "Double Hash" Strategy
We use two different hashes for two different purposes derived from the same cookie.

#### A. The "Post/Like" Hash (Publicly Visible ID)
Used to identify authors of posts and likers.
*   `salt`: `SECRET_KEY_PUBLIC` (Server Env Var).
*   **Formula**: `SHA256(anon_id + SECRET_KEY_PUBLIC)`
*   **Usage**: Stored in `posts.author_hash` and `likes.client_hash`.
*   **Privacy**: Stable. If a user posts twice, people can see it's the same author (e.g., "OP"). This is desired behavior for a board.

#### B. The "Moderation" Hash (Admin Only)
Used to ban users.
*   Actually, for this simple stack, **we can use the same hash (A)**.
*   **Ban Logic**: Admin bans `author_hash`. Middleware checks if `SHA256(current_cookie)` is in the `banned_users` table.

---

## 3. Implementation Logic

### Middleware (`app/middleware.py`)
```python
async def auth_middleware(request: Request, call_next):
    # 1. Get Cookie
    anon_id = request.cookies.get("anon_id")
    
    # 2. If missing, generate new
    if not anon_id:
        anon_id = str(uuid.uuid4())
        response = await call_next(request)
        response.set_cookie(
            key="anon_id", 
            value=anon_id,
            httponly=True,
            max_age=315360000 # 10 years
        )
        return response
        
    # 3. Attach hashed ID to request state for endpoints to use
    request.state.user_hash = hashlib.sha256(f"{anon_id}{SECRET_KEY}".encode()).hexdigest()
    
    return await call_next(request)
```

### Preventing Double Likes
*   **Logic**: DB Constraint `PRIMARY KEY (post_id, client_hash)`.
*   **Action**: If a user hits "Like":
    1.  Endpoint gets `state.user_hash`.
    2.  Tries `INSERT INTO likes ...`.
    3.  If IntegrityError (Duplicate Key), ignore or toggle (unlike).

### Privacy Summary
*   **Browser**: Has `anon_id` (UUID).
*   **Database**: Has `Hash(anon_id)`.
*   **Network**: Cookie sent encrypted (HTTPS).
*   **Logs**: No IP logging configured.
