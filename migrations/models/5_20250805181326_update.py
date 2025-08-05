from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "comments" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "content" VARCHAR(50) NOT NULL,
    "parent_comment_id" BIGINT REFERENCES "comments" ("id") ON DELETE CASCADE,
    "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "datasharemodel" (
    "id" SERIAL NOT NULL PRIMARY KEY
);
        CREATE TABLE IF NOT EXISTS "free_boards" (
    "image_url" VARCHAR(255),
    "post_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "posts" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "likes" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "posts" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(20) NOT NULL,
    "content" VARCHAR(500) NOT NULL,
    "category" VARCHAR(5) NOT NULL,
    "view_count" BIGINT NOT NULL DEFAULT 0,
    "like_count" BIGINT NOT NULL DEFAULT 0,
    "comment_count" BIGINT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "deleted_at" TIMESTAMPTZ,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "posts"."category" IS 'STUDY: study\nFREE: free\nSHARE: share';
        CREATE TABLE IF NOT EXISTS "study_recruitments" (
    "recruit_start" TIMESTAMPTZ NOT NULL,
    "recruit_end" TIMESTAMPTZ NOT NULL,
    "study_start" TIMESTAMPTZ NOT NULL,
    "study_end" TIMESTAMPTZ NOT NULL,
    "max_member" INT NOT NULL,
    "post_id" BIGINT NOT NULL PRIMARY KEY REFERENCES "posts" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "refresh_tokens" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "token" TEXT NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "revoked" BOOL NOT NULL DEFAULT False,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "social_accounts" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "provider" VARCHAR(6) NOT NULL,
    "provider_id" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON COLUMN "social_accounts"."provider" IS 'GOOGLE: google\nKAKAO: kakao';
        CREATE TABLE IF NOT EXISTS "users" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "nickname" VARCHAR(8) NOT NULL UNIQUE,
    "profile_image_url" VARCHAR(255),
    "is_active" BOOL NOT NULL DEFAULT True,
    "is_superuser" BOOL NOT NULL DEFAULT False,
    "social_account_id" BIGINT NOT NULL REFERENCES "social_accounts" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "posts";
        DROP TABLE IF EXISTS "refresh_tokens";
        DROP TABLE IF EXISTS "social_accounts";
        DROP TABLE IF EXISTS "users";
        DROP TABLE IF EXISTS "comments";
        DROP TABLE IF EXISTS "datasharemodel";
        DROP TABLE IF EXISTS "likes";
        DROP TABLE IF EXISTS "study_recruitments";
        DROP TABLE IF EXISTS "free_boards";"""
