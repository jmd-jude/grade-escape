#!/bin/bash

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Grade Escape MVP"

# Add remote repository
git remote add origin https://github.com/jmd-jude/grade-escape.git

# Set main as default branch (GitHub standard)
git branch -M main

# Push to GitHub
git push -u origin main

echo "Git repository setup complete!"
echo "Next steps:"
echo "1. Go to Streamlit Cloud (https://share.streamlit.io)"
echo "2. Connect to your GitHub repository"
echo "3. Add the following secrets in Streamlit Cloud settings:"
echo "   - OPENAI_API_KEY"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_KEY"
echo "   - SUPABASE_SERVICE_KEY"
echo "   - STORAGE_BUCKET"
