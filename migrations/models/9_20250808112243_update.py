from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "free_boards" ALTER COLUMN "image_url" TYPE TEXT USING "image_url"::TEXT;
        ALTER TABLE "users" ALTER COLUMN "profile_image_url" TYPE TEXT USING "profile_image_url"::TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ALTER COLUMN "profile_image_url" TYPE VARCHAR(255) USING "profile_image_url"::VARCHAR(255);
        ALTER TABLE "free_boards" ALTER COLUMN "image_url" TYPE VARCHAR(255) USING "image_url"::VARCHAR(255);"""
