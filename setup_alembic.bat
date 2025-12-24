@echo off
echo Setting up Alembic for database migrations...

mkdir alembic 2>nul
mkdir alembic\versions 2>nul

echo Alembic directories created successfully!
echo.
echo Next steps:
echo 1. Run: alembic init alembic (if not using Prisma)
echo 2. Or use: prisma migrate dev (recommended for Prisma)
echo.
echo Note: StockFlow Pro uses Prisma, so alembic is optional.
echo Use 'prisma db push' for schema sync in development.
pause
