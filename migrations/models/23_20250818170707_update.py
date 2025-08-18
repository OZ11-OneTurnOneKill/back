from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "ai_document_summaries" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(200) NOT NULL,
    "input_type" VARCHAR(20) NOT NULL DEFAULT 'text',
    "input_data" TEXT NOT NULL,
    "file_url" TEXT,
    "summary_type" VARCHAR(20) NOT NULL DEFAULT 'general',
    "output_data" TEXT,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "ai_document_summaries"."title" IS '요약 제목';
COMMENT ON COLUMN "ai_document_summaries"."input_type" IS '입력 타입 (text, url, file)';
COMMENT ON COLUMN "ai_document_summaries"."input_data" IS '원본 자료 (텍스트 또는 URL)';
COMMENT ON COLUMN "ai_document_summaries"."file_url" IS '업로드된 파일 URL';
COMMENT ON COLUMN "ai_document_summaries"."summary_type" IS '요약 유형 (general, keywords, qa, study)';
COMMENT ON COLUMN "ai_document_summaries"."output_data" IS 'AI 요약 결과 (JSON)';
COMMENT ON COLUMN "ai_document_summaries"."user_id" IS '유저 식별자 / FK';
COMMENT ON TABLE "ai_document_summaries" IS 'AI 자료 요약 테이블';
        CREATE TABLE IF NOT EXISTS "post_view_daily" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "day" DATE NOT NULL,
    "views" INT NOT NULL DEFAULT 0,
    "post_id" BIGINT NOT NULL REFERENCES "posts" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_post_view_d_post_id_56cd8c" UNIQUE ("post_id", "day")
);
CREATE INDEX IF NOT EXISTS "idx_post_view_d_day_ab884a" ON "post_view_daily" ("day");
CREATE INDEX IF NOT EXISTS "idx_post_view_d_post_id_56cd8c" ON "post_view_daily" ("post_id", "day");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "ai_document_summaries";
        DROP TABLE IF EXISTS "post_view_daily";"""
