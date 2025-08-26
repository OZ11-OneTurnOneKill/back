from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 1) post_id 먼저 추가 (nullable)
    ALTER TABLE "notifications" ADD COLUMN IF NOT EXISTS "post_id" BIGINT;

    -- 2) type은 nullable로 먼저 추가 (NOT NULL 금지)
    ALTER TABLE "notifications" ADD COLUMN IF NOT EXISTS "type" VARCHAR(11);

    -- 3) 과거 데이터 백필
    --    과거 알림은 신청 알림(application)만 있었다고 가정
    UPDATE "notifications" SET "type"='application' WHERE "type" IS NULL AND "application_id" IS NOT NULL;
    --    혹시 post_id가 이미 있는 데이터가 있다면 like로 지정
    UPDATE "notifications" SET "type"='like'        WHERE "type" IS NULL AND "post_id" IS NOT NULL;
    --    그래도 NULL이면 application으로 통일
    UPDATE "notifications" SET "type"='application' WHERE "type" IS NULL;

    -- 4) 이제 NOT NULL 적용
    ALTER TABLE "notifications" ALTER COLUMN "type" SET NOT NULL;

    -- 5) application_id 는 NULL 허용
    ALTER TABLE "notifications" ALTER COLUMN "application_id" DROP NOT NULL;

    -- 6) FK & 인덱스
    ALTER TABLE "notifications" DROP CONSTRAINT IF EXISTS "fk_notifica_posts_84a9d1f2";
    ALTER TABLE "notifications"
      ADD CONSTRAINT "fk_notifica_posts_84a9d1f2"
      FOREIGN KEY ("post_id") REFERENCES "posts" ("id") ON DELETE CASCADE;

    CREATE INDEX IF NOT EXISTS "idx_notificatio_post_id_af941b" ON "notifications" ("post_id");
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    DROP INDEX IF EXISTS "idx_notificatio_post_id_af941b";
    ALTER TABLE "notifications" DROP CONSTRAINT IF EXISTS "fk_notifica_posts_84a9d1f2";

    -- 원복: type 컬럼 제거(제약 먼저 풀림)
    ALTER TABLE "notifications" ALTER COLUMN "type" DROP NOT NULL;
    ALTER TABLE "notifications" DROP COLUMN IF EXISTS "type";

    -- post_id 제거
    ALTER TABLE "notifications" DROP COLUMN IF EXISTS "post_id";

    -- application_id 다시 NOT NULL
    ALTER TABLE "notifications" ALTER COLUMN "application_id" SET NOT NULL;
    """
