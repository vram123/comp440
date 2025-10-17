
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
