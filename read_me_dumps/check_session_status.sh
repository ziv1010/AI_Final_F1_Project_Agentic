#!/bin/bash

# Get the latest session ID from backend logs or from active sessions
SESSION_ID=$1

if [ -z "$SESSION_ID" ]; then
    echo "Usage: ./check_session_status.sh <session_id>"
    echo "Example: ./check_session_status.sh session_1765219686_0"
    exit 1
fi

echo "Checking status for session: $SESSION_ID"
echo ""

curl -s "http://localhost:5010/api/session/$SESSION_ID" | python3 -m json.tool
