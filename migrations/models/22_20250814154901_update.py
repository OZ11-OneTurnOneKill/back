from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "free_images" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "image_url" TEXT NOT NULL,
    "image_key" TEXT NOT NULL,
    "mime_type" VARCHAR(100) NOT NULL,
    "size_bytes" BIGINT NOT NULL,
    "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_free_images_post_id_0ba202" ON "free_images" ("post_id");
CREATE INDEX IF NOT EXISTS "idx_free_images_post_id_022347" ON "free_images" ("post_id", "id");
COMMENT ON TABLE "free_images" IS '자유게시판 이미지 첨부 (1:N)';
        CREATE TABLE IF NOT EXISTS "share_files" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "file_url" TEXT NOT NULL,
    "file_key" TEXT NOT NULL,
    "mime_type" VARCHAR(150) NOT NULL,
    "size_bytes" BIGINT NOT NULL,
    "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_share_files_post_id_180bac" ON "share_files" ("post_id");
CREATE INDEX IF NOT EXISTS "idx_share_files_post_id_ad031d" ON "share_files" ("post_id", "id");
COMMENT ON TABLE "share_files" IS '자료공유 파일 첨부 (1:N)';
        DROP TABLE IF EXISTS "data_shares";
        DROP TABLE IF EXISTS "free_boards";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "share_files";
        DROP TABLE IF EXISTS "free_images";"""
