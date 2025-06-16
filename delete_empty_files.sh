#!/bin/bash

# Script to find and delete all empty files in the project directory
# For Ubuntu/Linux systems

echo "🔍 Finding and deleting empty files in the project..."
echo "=================================================="

# Change to the project directory
cd /home/dante/Desktop/adk-stuff

# Find all empty files (0 bytes) and list them first
echo "📋 Empty files found:"
find . -type f -size 0 -print

echo ""
echo "🗑️  Deleting empty files..."

# Count empty files before deletion
empty_count=$(find . -type f -size 0 | wc -l)

if [ $empty_count -eq 0 ]; then
    echo "✅ No empty files found!"
else
    echo "Found $empty_count empty files. Deleting..."
    
    # Delete all empty files
    find . -type f -size 0 -delete
    
    echo "✅ Deleted $empty_count empty files!"
fi

echo ""
echo "🔍 Checking for empty directories..."

# Find empty directories (excluding .git and other system directories)
empty_dirs=$(find . -type d -empty -not -path "./.git*" -not -path "./node_modules*" -not -path "./__pycache__*" | wc -l)

if [ $empty_dirs -eq 0 ]; then
    echo "✅ No empty directories found!"
else
    echo "📋 Empty directories found:"
    find . -type d -empty -not -path "./.git*" -not -path "./node_modules*" -not -path "./__pycache__*" -print
    
    echo ""
    read -p "Do you want to delete empty directories too? (y/N): " delete_dirs
    
    if [[ $delete_dirs =~ ^[Yy]$ ]]; then
        find . -type d -empty -not -path "./.git*" -not -path "./node_modules*" -not -path "./__pycache__*" -delete
        echo "✅ Deleted empty directories!"
    else
        echo "ℹ️  Kept empty directories."
    fi
fi

echo ""
echo "🧹 Cleanup completed!"
echo "=================================================="

# Show final project structure
echo "📁 Current project structure:"
find . -type f -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.css" -o -name "*.md" -o -name "*.sh" -o -name "*.sql" | head -20

echo ""
echo "✅ All empty files have been removed from your Ubuntu system!"