from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP CONSTRAINT IF EXISTS "fk_users_social_a_a62b8825";
        ALTER TABLE "refresh_tokens" DROP CONSTRAINT IF EXISTS "fk_refresh__users_1c3fe0a4";
        ALTER TABLE "refresh_tokens" ADD CONSTRAINT "fk_refresh__users_1c3fe0a4" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_refresh_tok_user_id_9ddaa8" ON "refresh_tokens" ("user_id");
        ALTER TABLE "users" ADD CONSTRAINT "fk_users_social_a_a62b8825" FOREIGN KEY ("social_account_id") REFERENCES "social_accounts" ("id") ON DELETE CASCADE;
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_users_social__f46b10" ON "users" ("social_account_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_refresh_tok_user_id_9ddaa8";
        ALTER TABLE "refresh_tokens" DROP CONSTRAINT IF EXISTS "fk_refresh__users_1c3fe0a4";
        DROP INDEX IF EXISTS "uid_users_social__f46b10";
        ALTER TABLE "users" DROP CONSTRAINT IF EXISTS "fk_users_social_a_a62b8825";
        ALTER TABLE "users" ADD CONSTRAINT "fk_users_social_a_a62b8825" FOREIGN KEY ("social_account_id") REFERENCES "social_accounts" ("id") ON DELETE CASCADE;
        ALTER TABLE "refresh_tokens" ADD CONSTRAINT "fk_refresh__users_1c3fe0a4" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE;"""
