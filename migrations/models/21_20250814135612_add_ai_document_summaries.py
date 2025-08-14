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

        -- 인덱스 (조회 패턴 기준 권장)
        CREATE INDEX IF NOT EXISTS "idx_docsum_user" ON "ai_document_summaries" ("user_id");
        CREATE INDEX IF NOT EXISTS "idx_docsum_created_at" ON "ai_document_summaries" ("created_at" DESC);
        CREATE INDEX IF NOT EXISTS "idx_docsum_summary_user" ON "ai_document_summaries" ("summary_type", "user_id");

        -- (선택) 주석
        COMMENT ON TABLE "ai_document_summaries" IS 'AI 자료 요약 테이블';
        COMMENT ON COLUMN "ai_document_summaries"."user_id" IS '유저 식별자 / FK';
        COMMENT ON COLUMN "ai_document_summaries"."title" IS '요약 제목';
        COMMENT ON COLUMN "ai_document_summaries"."input_type" IS '입력 타입 (text, url, file)';
        COMMENT ON COLUMN "ai_document_summaries"."input_data" IS '원본 자료 (텍스트 또는 URL)';
        COMMENT ON COLUMN "ai_document_summaries"."file_url" IS '업로드된 파일 URL';
        COMMENT ON COLUMN "ai_document_summaries"."summary_type" IS '요약 유형 (general, keywords, qa, study)';
        COMMENT ON COLUMN "ai_document_summaries"."output_data" IS 'AI 요약 결과 (JSON)';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "ai_document_summaries";
    """
