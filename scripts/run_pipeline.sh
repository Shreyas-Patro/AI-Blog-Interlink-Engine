#!/bin/bash
# Convenience script to run the full pipeline
set -e

echo "=== AI Link Engine MVP ==="
echo ""

# Step 1: Create test posts if they don't exist
if [ ! -d "test_posts" ]; then
  echo "Creating test posts..."
  python scripts/seed.py
fi

# Step 2: Run pipeline
echo "Running pipeline on test_posts/..."
python -m link_engine.cli run ./test_posts

# Step 3: Show status
echo ""
python -m link_engine.cli status

# Step 4: Launch dashboard
echo ""
echo "Launching dashboard..."
python -m link_engine.cli dashboard