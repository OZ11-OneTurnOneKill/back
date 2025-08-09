from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- ✅ 음수 방지 CHECK (posts)
    ALTER TABLE "posts"
      ADD CONSTRAINT "chk_posts_view_count_nonneg"    CHECK (view_count    >= 0),
      ADD CONSTRAINT "chk_posts_like_count_nonneg"    CHECK (like_count    >= 0),
      ADD CONSTRAINT "chk_posts_comment_count_nonneg" CHECK (comment_count >= 0);

    -- ✅ 음수 방지 CHECK (study_recruitments)
    ALTER TABLE "study_recruitments"
      ADD CONSTRAINT "chk_study_recruitments_max_member_nonneg" CHECK (max_member >= 0);

    -- ✅ 좋아요 중복 방지 UNIQUE (likes)
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_likes_post_user'
      ) THEN
        ALTER TABLE "likes"
          ADD CONSTRAINT "uq_likes_post_user" UNIQUE ("post_id","user_id");
      END IF;
    END $$;

    -- ✅ 인덱스 (쿼리 빈도 높은 것 위주)
    CREATE INDEX IF NOT EXISTS "idx_posts_category"   ON "posts" ("category");
    CREATE INDEX IF NOT EXISTS "idx_posts_user"       ON "posts" ("user_id");
    CREATE INDEX IF NOT EXISTS "idx_posts_created_at" ON "posts" ("created_at" DESC);
    CREATE INDEX IF NOT EXISTS "idx_sr_recruit_end"   ON "study_recruitments" ("recruit_end");
    CREATE INDEX IF NOT EXISTS "idx_likes_post"       ON "likes" ("post_id");
    CREATE INDEX IF NOT EXISTS "idx_likes_user"       ON "likes" ("user_id");
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 인덱스 롤백
    DROP INDEX IF EXISTS "idx_likes_user";
    DROP INDEX IF EXISTS "idx_likes_post";
    DROP INDEX IF EXISTS "idx_sr_recruit_end";
    DROP INDEX IF EXISTS "idx_posts_created_at";
    DROP INDEX IF EXISTS "idx_posts_user";
    DROP INDEX IF EXISTS "idx_posts_category";

    -- UNIQUE 롤백
    ALTER TABLE "likes" DROP CONSTRAINT IF EXISTS "uq_likes_post_user";

    -- CHECK 롤백
    ALTER TABLE "study_recruitments" DROP CONSTRAINT IF EXISTS "chk_study_recruitments_max_member_nonneg";
    ALTER TABLE "posts" DROP CONSTRAINT IF EXISTS "chk_posts_comment_count_nonneg";
    ALTER TABLE "posts" DROP CONSTRAINT IF EXISTS "chk_posts_like_count_nonneg";
    ALTER TABLE "posts" DROP CONSTRAINT IF EXISTS "chk_posts_view_count_nonneg";
    """
