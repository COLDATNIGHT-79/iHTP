# Database Schema Design (PostgreSQL)

## Overview
This schema is designed for **Supabase (PostgreSQL)**. It prioritizes simplicity and leverages Postgres-specific features (Arrays) to reduce table count.

### 1. Tables

#### `posts`
The core content table.
*   **Why specific columns?**:
    *   `tags`: SQL Array `TEXT[]` allows storing up to 3 tags without a complex many-to-many join.
    *   `moderation_status`: Enum/Text to handle the "Warning Label" state.
    *   `moderation_reason`: The text displayed on the red warning card.

```sql
CREATE TYPE moderation_status_enum AS ENUM ('active', 'blocked');

CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content
    content TEXT NOT NULL CHECK (length(content) > 0),
    tags TEXT[] CHECK (array_length(tags, 1) <= 3), -- Enforce max 3 tags
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    author_hash TEXT NOT NULL, -- Hashed cookie ID for rate limiting/logging
    
    -- Engagement (Denormalized for simple sorting)
    like_count INT DEFAULT 0,
    
    -- Moderation (The "Red Warning" System)
    status moderation_status_enum DEFAULT 'active',
    moderation_reason TEXT -- E.g., "Violates Rule 1: Incitement to Violence"
);

-- Index for searching (Full Text Search)
CREATE INDEX posts_content_idx ON posts USING GIN (to_tsvector('english', content));
-- Index for sorting
CREATE INDEX posts_created_at_idx ON posts (created_at DESC);
```

#### `likes`
Tracks unique interactions to prevent double-voting.
*   **Privacy**: Stores a hash of the user's cookie, not PII.

```sql
CREATE TABLE likes (
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    client_hash TEXT NOT NULL, -- Distinct from author_hash, represents the "liker"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (post_id, client_hash) -- Composite PK prevents duplicate likes from same device
);
```

### 2. Logic & Constraints

*   **Soft Deletion (Blocking)**:
    *   We DO NOT use `DELETE` for banned content.
    *   Instead, we `UPDATE posts SET status = 'blocked', moderation_reason = '...' WHERE id = ...`.
    *   The frontend checks `status`. If `blocked`, it renders the **Red Warning Component** but keeps the data loadable if requested.

*   **Tags**:
    *   Input: `["politics", "rant"]`
    *   Constraint `array_length <= 3` handles the limit natively in the DB.

*   **Dates**:
    *   `created_at` records the precise timestamp.
    *   Frontend formats this to "X hours ago" or "Jan 01, 2024".
