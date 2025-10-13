#!/bin/bash
echo "Taking screenshot using headless Chrome..."
docker run --rm --network host -v $(pwd):/workspace zenika/alpine-chrome:latest \
  --no-sandbox \
  --headless \
  --disable-gpu \
  --disable-dev-shm-usage \
  --window-size=1920,1080 \
  --screenshot=/workspace/valueverse-ui.png \
  http://localhost:3000/workspace

if [ -f "valueverse-ui.png" ]; then
  echo "Screenshot saved as valueverse-ui.png"
  echo "File size: $(ls -lh valueverse-ui.png | awk '{print $5}')"
else
  echo "Failed to create screenshot"
fi
