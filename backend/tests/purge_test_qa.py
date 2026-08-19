"""Utility: purge TEST_QA bookings created during automated testing."""
import asyncio
import os

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

env = dotenv_values("/app/backend/.env")
MONGO_URL = os.environ.get("MONGO_URL") or env.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME") or env.get("DB_NAME")


async def main():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    res = await db.bookings.delete_many({"full_name": {"$regex": "^TEST_QA"}})
    total = await db.bookings.count_documents({})
    print(f"deleted={res.deleted_count} remaining={total}")
    client.close()


asyncio.run(main())
