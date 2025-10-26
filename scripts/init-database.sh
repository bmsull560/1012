#!/bin/bash
# Database Initialization Script for ValueVerse Platform
# This script sets up the PostgreSQL database and runs all migrations

set -e

echo "🚀 ValueVerse Database Initialization Script"
echo "==========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults if not provided
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
DB_NAME=${DB_NAME:-valueverse}

echo "📊 Database Configuration:"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c '\q' 2>/dev/null; do
  echo "  PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Create database if it doesn't exist
echo "📦 Creating database if not exists..."
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $DB_NAME'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
EOSQL

# Run migrations
echo "🔄 Running database migrations..."
MIGRATION_DIR="billing-system/migrations"

if [ -d "$MIGRATION_DIR" ]; then
    for migration in $(ls $MIGRATION_DIR/*.sql | sort); do
        echo "  Applying migration: $(basename $migration)"
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration"
    done
else
    echo "⚠️  No migrations directory found at $MIGRATION_DIR"
fi

# Create initial admin user (if using local auth instead of Supabase)
echo "👤 Creating initial admin user..."
PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<-EOSQL
    -- Create users table if not exists
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Insert admin user if not exists
    INSERT INTO users (email, password_hash, role)
    SELECT 'admin@valueverse.com', 
           crypt('admin123', gen_salt('bf')), 
           'admin'
    WHERE NOT EXISTS (
        SELECT 1 FROM users WHERE email = 'admin@valueverse.com'
    );
EOSQL

echo "✨ Database initialization complete!"
echo ""
echo "📝 Summary:"
echo "  - Database '$DB_NAME' is ready"
echo "  - All migrations have been applied"
echo "  - Admin user created (admin@valueverse.com / admin123)"
echo ""
echo "⚠️  Remember to change the admin password in production!"
