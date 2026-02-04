# Tech Stack Proposal: Anonymous Social Board

## Core Philosophy
**"Simple, Text-Heavy, Low-Maintenance"**
We prioritize a stack that requires minimal client-side state management, uses a robust hosted database (for free), and leverages Python for all logic.

---

## 1. The Stack (Python-Centric)

| Component | Choice | Why? |
| :--- | :--- | :--- |
| **Language** | **Python 3.10+** | Requested preference. Robust ecosystem. |
| **Framework** | **FastAPI** | Modern, strictly typed (Pydantic), auto-documentation (Swagger UI), and very fast (ASGI). Better long-term maintenance than Flask. |
| **Frontend** | **HTMX + Jinja2** | **Key Simplifier**. Removing React/Vue eliminates the build step and "API Glue" code. We render HTML on the server (Jinja2) and swap parts of the page dynamically with HTMX. |
| **Styling** | **TailwindCSS (CDN)** | Utility-first CSS. Used via CDN for dev simplicity (or simple CLI build) to avoid complex node pipelines. |
| **Database** | **PostgreSQL (Supabase)** | **Generous Free Tier** (500MB is huge for text). Native Full-Text Search. Rock-solid stability. |
| **Hosting** | **Render / Railway** | Both offer excellent free tiers for Python web services. |

---

## 2. Feature Implementation Strategy

### A. Authentication (No Accounts)
*   **Mechanism**: Signed HTTP-Only Cookies.
*   **Flow**:
    1.  User visits site.
    2.  Middleware checks for `anon_token`.
    3.  If missing, generate a cryptographic UUID, sign it with `SECRET_KEY`, and set cookie (10-year expiry).
    4.  All database writes (posts, likes) record this `anon_id`.

### B. Board & Public Posts
*   **Schema**: `posts` table with `id`, `content`, `created_at`, `author_hash`, `warning_label` (nullable).
*   **Rendering**: Server-side Jinja templates.
*   **Speed**: HTMX "Infinite Scroll" or "Load More" button to fetch next page of HTML partials.

### C. Search
*   **Tech**: PostgreSQL `tsvector` / `tsquery`.
*   **Efficiency**: No external search engine needed. Postgres FTS is incredibly fast for < 10M rows.
*   **Query**: `SELECT * FROM posts WHERE to_tsvector(content) @@ plainto_tsquery(:query);`

### D. Moderation (Admin Only)
*   **Access**: Hardcoded Admin Login URL (e.g., `/admin/login`) requiring a secure password set in Environment Variables.
*   **Action**: Admin interface allows setting the `warning_label` column on posts.

---

## 3. Why this wins on "Simplicity"?
1.  **One Codebase**: Everything is Python. No `package.json`, no `node_modules` hell.
2.  **No "State Sync"**: The server is the source of truth. The UI just reflects it.
3.  **Free Scaling**: Supabase + Render Free Tiers can handle thousands of daily users required for text-based apps without costing $0.
