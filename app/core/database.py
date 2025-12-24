from prisma import Prisma
from contextlib import asynccontextmanager

prisma = Prisma()

async def connect_db():
    await prisma.connect()

async def disconnect_db():
    await prisma.disconnect()

@asynccontextmanager
async def get_db():
    try:
        yield prisma
    finally:
        pass
