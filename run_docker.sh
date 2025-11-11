#!/bin/bash

set -e  # Stop if any command fails

URL="http://localhost:8050"

echo "Building and starting Dashboard STAMM container..."
docker compose up --build -d

echo "Waiting for Dash app to start..."

# Wait until the URL responds (max 60 seconds)
MAX_WAIT=60
COUNTER=0

while ! curl -s --head --request GET "$URL" | grep "200 OK" > /dev/null; do
  sleep 2
  COUNTER=$((COUNTER + 2))
  echo "Waiting... ($COUNTER seconds)"
  if [ "$COUNTER" -ge "$MAX_WAIT" ]; then
    echo "App did not start within $MAX_WAIT seconds."
    echo "   You can check logs using: docker compose logs -f"
    exit 1
  fi
done

# Open the browser depending on the OS
echo "Opening $URL in your default browser..."
if which xdg-open > /dev/null; then
  xdg-open "$URL"
elif which open > /dev/null; then
  open "$URL"
elif which start > /dev/null; then
  start "$URL"
else
  echo "Dashboard STAMM running at $URL"
fi

echo "Dashboard STAMM is up and running!"
