from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" DROP CONSTRAINT IF EXISTS "fk_users_social_a_a62b8825";
        ALTER TABLE "users" ADD "email" VARCHAR(50) NOT NULL UNIQUE;
        ALTER TABLE "users" ADD "provider_id" VARCHAR(50) NOT NULL UNIQUE;
        ALTER TABLE "users" ADD "provider" VARCHAR(6) NOT NULL;
        ALTER TABLE "users" DROP COLUMN "social_account_id";
        DROP TABLE IF EXISTS "social_accounts";
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_users_email_133a6f" ON "users" ("email");
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_users_provide_f1bddf" ON "users" ("provider_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_users_provide_f1bddf";
        DROP INDEX IF EXISTS "uid_users_email_133a6f";
        ALTER TABLE "users" ADD "social_account_id" BIGINT NOT NULL UNIQUE;
        ALTER TABLE "users" DROP COLUMN "email";
        ALTER TABLE "users" DROP COLUMN "provider_id";
        ALTER TABLE "users" DROP COLUMN "provider";
        ALTER TABLE "users" ADD CONSTRAINT "fk_users_social_a_a62b8825" FOREIGN KEY ("social_account_id") REFERENCES "social_accounts" ("id") ON DELETE CASCADE;"""
