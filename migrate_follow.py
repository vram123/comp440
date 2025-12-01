# migrate_follow.py — ensure follow table exists
from db import get_db

DDL = """
CREATE TABLE IF NOT EXISTS follow (
  follower TEXT NOT NULL,
  followee TEXT NOT NULL,
  PRIMARY KEY (follower, followee),
  FOREIGN KEY (follower) REFERENCES user(username),
  FOREIGN KEY (followee) REFERENCES user(username)
);
"""

if __name__ == "__main__":
    with get_db() as conn:
        conn.executescript(DDL)
        conn.commit()
    print("follow table ensured.")
