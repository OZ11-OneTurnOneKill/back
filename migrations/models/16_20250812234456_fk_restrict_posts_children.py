from tortoise import BaseDBAsyncClient

async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- study_recruitments → posts(id)
    ALTER TABLE "study_recruitments" DROP CONSTRAINT IF EXISTS "study_recruitments_post_id_fkey";
    ALTER TABLE "study_recruitments" DROP CONSTRAINT IF EXISTS "fk_study_recruitments_post";
    ALTER TABLE "study_recruitments"
      ADD CONSTRAINT "fk_study_recruitments_post"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE RESTRICT;

    -- data_shares → posts(id)
    ALTER TABLE "data_shares" DROP CONSTRAINT IF EXISTS "fk_data_sha_posts_41afd1ef";
    ALTER TABLE "data_shares" DROP CONSTRAINT IF EXISTS "fk_data_shares_post";
    ALTER TABLE "data_shares"
      ADD CONSTRAINT "fk_data_shares_post"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE RESTRICT;

    -- free_boards → posts(id)
    ALTER TABLE "free_boards" DROP CONSTRAINT IF EXISTS "free_boards_post_id_fkey";
    ALTER TABLE "free_boards" DROP CONSTRAINT IF EXISTS "fk_free_boards_post";
    ALTER TABLE "free_boards"
      ADD CONSTRAINT "fk_free_boards_post"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE RESTRICT;
    """

async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
    -- 되돌리기: RESTRICT → CASCADE

    -- study_recruitments
    ALTER TABLE "study_recruitments" DROP CONSTRAINT IF EXISTS "fk_study_recruitments_post";
    ALTER TABLE "study_recruitments"
      ADD CONSTRAINT "study_recruitments_post_id_fkey"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;

    -- data_shares
    ALTER TABLE "data_shares" DROP CONSTRAINT IF EXISTS "fk_data_shares_post";
    ALTER TABLE "data_shares"
      ADD CONSTRAINT "fk_data_sha_posts_41afd1ef"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;

    -- free_boards
    ALTER TABLE "free_boards" DROP CONSTRAINT IF EXISTS "fk_free_boards_post";
    ALTER TABLE "free_boards"
      ADD CONSTRAINT "free_boards_post_id_fkey"
      FOREIGN KEY ("post_id") REFERENCES "posts"("id") ON DELETE CASCADE;
    """
