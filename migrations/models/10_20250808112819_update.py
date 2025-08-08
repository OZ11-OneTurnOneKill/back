from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "datasharemodel" RENAME TO "data_shares";
        ALTER TABLE "data_shares" RENAME COLUMN "id" TO "post_id";
        ALTER TABLE "data_shares" ALTER COLUMN "post_id" TYPE BIGINT USING "post_id"::BIGINT;
        ALTER TABLE "data_shares" ADD "file_url" TEXT;
        ALTER TABLE "data_shares" ADD CONSTRAINT "fk_data_sha_posts_41afd1ef" FOREIGN KEY ("post_id") REFERENCES "posts" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "data_shares" DROP CONSTRAINT IF EXISTS "fk_data_sha_posts_41afd1ef";
        ALTER TABLE "data_shares" RENAME TO "datasharemodel";
        ALTER TABLE "data_shares" RENAME COLUMN "post_id" TO "id";
        ALTER TABLE "data_shares" ALTER COLUMN "id" TYPE INT USING "id"::INT;
        ALTER TABLE "data_shares" DROP COLUMN "file_url";"""
