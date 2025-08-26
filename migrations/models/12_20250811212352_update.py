from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 1) study_applications 먼저
    CREATE TABLE IF NOT EXISTS "study_applications" (
        "id" BIGSERIAL NOT NULL PRIMARY KEY,
        "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "status" VARCHAR(10) NOT NULL DEFAULT 'recruiting',
        "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE,
        "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
        CONSTRAINT "uid_study_appli_post_id_user_id" UNIQUE ("post_id","user_id")
    );
    CREATE INDEX IF NOT EXISTS "idx_study_appli_post_id" ON "study_applications" ("post_id");
    CREATE INDEX IF NOT EXISTS "idx_study_appli_user_id" ON "study_applications" ("user_id");
    CREATE INDEX IF NOT EXISTS "idx_study_appli_status_post_id" ON "study_applications" ("status","post_id");
    COMMENT ON COLUMN "study_applications"."status" IS 'recruiting|completed';

    -- 2) notifications 나중
    CREATE TABLE IF NOT EXISTS "notifications" (
        "id" BIGSERIAL NOT NULL PRIMARY KEY,
        "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "message" VARCHAR(255) NOT NULL,
        "is_read" BOOL NOT NULL DEFAULT False,
        "application_id" BIGINT NOT NULL REFERENCES "study_applications" ("id") ON DELETE CASCADE,
        "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS "idx_notifications_user_isread" ON "notifications" ("user_id","is_read");
    CREATE INDEX IF NOT EXISTS "idx_notifications_application_id" ON "notifications" ("application_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "notifications";
        DROP TABLE IF EXISTS "study_applications";"""
