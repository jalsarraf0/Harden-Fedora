#!/bin/bash

REPO_DIR="/home/jalsarraf/git/Harden-Fedora"
CORRECT_NAME="jalsarraf0"
CORRECT_EMAIL="jalsarraf0@gmail.com"
REMOTE="origin"
BRANCH="main"
REMOTE_URL="git@github.com:jalsarraf0/Harden-Fedora.git"

cd "$REPO_DIR" || { echo "❌ Repository not found."; exit 1; }

# Create the correct Python callback script using direct assignments
CALLBACK_SCRIPT=$(mktemp)
cat <<EOF > "$CALLBACK_SCRIPT"
def commit_callback(commit):
    commit.author_name = b"$CORRECT_NAME"
    commit.author_email = b"$CORRECT_EMAIL"
    commit.committer_name = b"$CORRECT_NAME"
    commit.committer_email = b"$CORRECT_EMAIL"
EOF

# Run git-filter-repo forcing all commits to use the correct author and committer
git filter-repo --force --commit-callback "$CALLBACK_SCRIPT"

# Clean up temp script
rm -f "$CALLBACK_SCRIPT"

# Re-add remote
git remote remove "$REMOTE" 2>/dev/null
git remote add "$REMOTE" "$REMOTE_URL"

# Force push cleaned history
git push --force --tags "$REMOTE" "$BRANCH"

# Final verification
if git log --pretty=format:"%h | %an | %ae | %cn | %ce" | grep -i "ezwow"; then
    echo "❌ ezwow still found in history! Manual inspection required."
else
    echo "✔️ Clean history confirmed. 'ezwow' fully removed."
fi
