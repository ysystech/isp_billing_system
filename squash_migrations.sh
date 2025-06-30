#!/bin/bash
# Squash all migrations and start fresh
# WARNING: This will delete all data!

echo "🚨 WARNING: This will delete all migrations and reset the database!"
echo "Make sure you have backed up any important data."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted."
    exit 1
fi

echo "📁 Step 1: Removing old migration files..."
find apps -path "*/migrations/*.py" -not -name "__init__.py" -delete
echo "✅ Old migrations removed"

echo ""
echo "📝 Step 2: Creating fresh migrations..."
make manage ARGS="makemigrations"

echo ""
echo "🚀 Step 3: Running migrations..."
make manage ARGS="migrate"
