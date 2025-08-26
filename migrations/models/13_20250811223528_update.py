from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    CREATE TABLE IF NOT EXISTS "ai_study_plans" (
        "id" BIGSERIAL NOT NULL PRIMARY KEY,
        "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "is_challenge" BOOL NOT NULL DEFAULT False,
        "input_data" TEXT NOT NULL,
        "output_data" TEXT,
        "start_date" TIMESTAMPTZ NOT NULL,
        "end_date" TIMESTAMPTZ NOT NULL,
        "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
    );
    COMMENT ON COLUMN "ai_study_plans"."is_challenge" IS '챌린지 수행 여부';
    COMMENT ON COLUMN "ai_study_plans"."input_data" IS '유저 질문 (프롬프트)';
    COMMENT ON COLUMN "ai_study_plans"."output_data" IS 'AI 답변';
    COMMENT ON COLUMN "ai_study_plans"."start_date" IS '공부 계획 일정 시작하는 날';
    COMMENT ON COLUMN "ai_study_plans"."end_date" IS '공부 계획 일정 끝나는 날';
    COMMENT ON COLUMN "ai_study_plans"."user_id" IS '유저 식별자 / FK';
    COMMENT ON TABLE "ai_study_plans" IS 'AI 학습계획 테이블';

    CREATE TABLE IF NOT EXISTS "ai_challenge_progress" (
        "id" BIGSERIAL NOT NULL PRIMARY KEY,
        "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        "status" VARCHAR(50),
        "challenge_image_url" TEXT,
        "study_plan_id" BIGINT NOT NULL REFERENCES "ai_study_plans" ("id") ON DELETE CASCADE,
        "user_id" BIGINT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
    );
    COMMENT ON COLUMN "ai_challenge_progress"."status" IS '챌린지 진행 상태 (진행 완료, 진행 중, 실패)';
    COMMENT ON COLUMN "ai_challenge_progress"."challenge_image_url" IS '챌린지 관련 이미지 저장';
    COMMENT ON COLUMN "ai_challenge_progress"."study_plan_id" IS '공부 계획 식별자 / FK';
    COMMENT ON COLUMN "ai_challenge_progress"."user_id" IS '유저 식별자 / FK';
    COMMENT ON TABLE "ai_challenge_progress" IS 'AI 챌린지 진행상황 테이블';

    CREATE INDEX IF NOT EXISTS "idx_ai_challenge_progress_user" ON "ai_challenge_progress" ("user_id");
    CREATE INDEX IF NOT EXISTS "idx_ai_challenge_progress_plan" ON "ai_challenge_progress" ("study_plan_id");
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP TABLE IF EXISTS "ai_challenge_progress";
    DROP TABLE IF EXISTS "ai_study_plans";
    """
