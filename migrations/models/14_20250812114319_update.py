from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "study_applications" ALTER COLUMN "status" SET DEFAULT 'pending';
        ALTER TABLE "study_applications" ALTER COLUMN "status" TYPE VARCHAR(8) USING "status"::VARCHAR(8);
        COMMENT ON COLUMN "study_applications"."status" IS 'pending: pending
approved: approved
rejected: rejected';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "study_applications" ALTER COLUMN "status" SET DEFAULT 'recruiting';
        COMMENT ON COLUMN "study_applications"."status" IS 'RECRUITING: recruiting
COMPLETED: completed';
        ALTER TABLE "study_applications" ALTER COLUMN "status" TYPE VARCHAR(10) USING "status"::VARCHAR(10);"""
