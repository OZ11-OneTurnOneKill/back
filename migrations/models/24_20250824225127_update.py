from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "notifications" ADD "actor_id" BIGINT;
        ALTER TABLE "notifications" ADD CONSTRAINT "fk_notifica_users_1d656d9e" FOREIGN KEY ("actor_id") REFERENCES "users" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "notifications" DROP CONSTRAINT IF EXISTS "fk_notifica_users_1d656d9e";
        ALTER TABLE "notifications" DROP COLUMN "actor_id";"""
