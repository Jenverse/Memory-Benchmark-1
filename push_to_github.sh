#!/bin/bash

# Script to push MemoryBench to GitHub repository
# Repository: Memory-Benchmark-1

echo "🚀 Pushing MemoryBench to GitHub..."
echo ""

# Set the repository URL
REPO_URL="https://github.com/Jenverse/Memory-Benchmark-1.git"

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "✅ Remote 'origin' already exists"
    echo "   Current URL: $(git remote get-url origin)"
    echo ""
    read -p "Do you want to update it to $REPO_URL? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin "$REPO_URL"
        echo "✅ Updated remote URL"
    fi
else
    echo "➕ Adding remote 'origin'..."
    git remote add origin "$REPO_URL"
    echo "✅ Remote added: $REPO_URL"
fi

echo ""
echo "📤 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "📍 Your repository is now at:"
    echo "   https://github.com/Jenverse/Memory-Benchmark-1"
    echo ""
    echo "🔗 Next step: Create anonymous mirror"
    echo "   1. Go to: https://anonymous.4open.science/"
    echo "   2. Enter: https://github.com/Jenverse/Memory-Benchmark-1"
    echo "   3. Get your anonymous URL for ICLR submission"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "   1. Repository exists on GitHub"
    echo "   2. You have push access"
    echo "   3. You're authenticated (try: gh auth login)"
fi

