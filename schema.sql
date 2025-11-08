
-- Database schema for COMP 440 Phase 1
DROP TABLE IF EXISTS user;
CREATE TABLE user (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL
);

-- === Phase 2 tables ===

-- Blogs
CREATE TABLE IF NOT EXISTS blog (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner TEXT NOT NULL,
  subject TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (owner) REFERENCES user(username)
);
CREATE INDEX IF NOT EXISTS idx_blog_owner_created ON blog(owner, created_at);

-- Tags (simple join table)
CREATE TABLE IF NOT EXISTS blog_tag (
  blog_id INTEGER NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY (blog_id, tag),
  FOREIGN KEY (blog_id) REFERENCES blog(id)
);
CREATE INDEX IF NOT EXISTS idx_tag_tag ON blog_tag(tag);

-- Comments
CREATE TABLE IF NOT EXISTS comment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  blog_id INTEGER NOT NULL,
  reviewer TEXT NOT NULL,
  sentiment TEXT NOT NULL CHECK (sentiment IN ('positive','negative')),
  description TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
  FOREIGN KEY (blog_id) REFERENCES blog(id),
  FOREIGN KEY (reviewer) REFERENCES user(username),
  UNIQUE (blog_id, reviewer) -- ≤1 comment per blog per user
);
CREATE INDEX IF NOT EXISTS idx_comment_reviewer_created ON comment(reviewer, created_at);
