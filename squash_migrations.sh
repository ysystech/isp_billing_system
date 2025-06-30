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
echo "🗄️  Step 3: Reset database? (y/N): "
read -p "" -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Resetting database..."
    docker-compose down -v
    docker-compose up -d db
    echo "Waiting for database to be ready..."
    sleep 5
    
    echo ""
    echo "🚀 Step 4: Running migrations..."
    make manage ARGS="migrate"
    
    echo ""
    echo "👤 Step 5: Create superuser? (y/N): "
    read -p "" -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        make manage ARGS="createsuperuser"
    fi
    
    echo ""
    echo "🔧 Step 6: Running initial setup..."
    make manage ARGS="initial_setup"
    
    echo ""
    echo "✅ Migration squashing complete!"
    echo ""
    echo "Next steps:"
    echo "1. Commit the new migration files: git add apps/*/migrations/0001_initial.py"
    echo "2. Start the server: make start"
    echo "3. Test the application"
else
    echo ""
    echo "⚠️  Migrations created but database not reset."
    echo "To apply migrations later, run: make manage ARGS='migrate'"
fi
