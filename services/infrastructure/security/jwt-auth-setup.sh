#!/bin/bash

# JWT Authentication Setup for Kong API Gateway
# Implements JWT-based authentication for all microservices

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Setting up JWT Authentication in Kong...${NC}"
echo ""

# Step 1: Create consumers
echo "Creating API consumers..."

# Admin consumer
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin-user",
    "custom_id": "admin-001"
  }' 2>/dev/null || true

# Frontend consumer
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{
    "username": "frontend-app",
    "custom_id": "frontend-001"
  }' 2>/dev/null || true

# Service-to-service consumer
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{
    "username": "internal-services",
    "custom_id": "internal-001"
  }' 2>/dev/null || true

echo -e "${GREEN}✓ Consumers created${NC}"

# Step 2: Generate JWT credentials
echo ""
echo "Generating JWT credentials..."

# Generate RSA key pair for JWT signing
openssl genrsa -out private.pem 2048 2>/dev/null
openssl rsa -in private.pem -outform PEM -pubout -out public.pem 2>/dev/null

# Create JWT credential for admin
ADMIN_KEY="admin-jwt-key-$(uuidgen)"
ADMIN_SECRET="admin-jwt-secret-$(uuidgen)"

curl -X POST http://localhost:8001/consumers/admin-user/jwt \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"$ADMIN_KEY\",
    \"secret\": \"$ADMIN_SECRET\",
    \"algorithm\": \"HS256\"
  }" 2>/dev/null || true

# Create JWT credential for frontend
FRONTEND_KEY="frontend-jwt-key-$(uuidgen)"
FRONTEND_SECRET="frontend-jwt-secret-$(uuidgen)"

curl -X POST http://localhost:8001/consumers/frontend-app/jwt \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"$FRONTEND_KEY\",
    \"secret\": \"$FRONTEND_SECRET\",
    \"algorithm\": \"HS256\"
  }" 2>/dev/null || true

echo -e "${GREEN}✓ JWT credentials created${NC}"

# Step 3: Enable JWT plugin globally
echo ""
echo "Enabling JWT authentication plugin..."

curl -X POST http://localhost:8001/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jwt",
    "config": {
      "key_claim_name": "iss",
      "secret_is_base64": false,
      "claims_to_verify": ["exp", "nbf"],
      "maximum_expiration": 3600,
      "header_names": ["Authorization"],
      "cookie_names": ["jwt_token"],
      "run_on_preflight": false
    }
  }' 2>/dev/null || true

echo -e "${GREEN}✓ JWT plugin enabled${NC}"

# Step 4: Add ACL plugin for authorization
echo ""
echo "Setting up ACL (Access Control List) plugin..."

curl -X POST http://localhost:8001/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "acl",
    "config": {
      "whitelist": ["admin", "user", "service"],
      "hide_groups_header": false
    }
  }' 2>/dev/null || true

# Add admin to admin group
curl -X POST http://localhost:8001/consumers/admin-user/acls \
  -H "Content-Type: application/json" \
  -d '{"group": "admin"}' 2>/dev/null || true

# Add frontend to user group
curl -X POST http://localhost:8001/consumers/frontend-app/acls \
  -H "Content-Type: application/json" \
  -d '{"group": "user"}' 2>/dev/null || true

# Add internal services to service group
curl -X POST http://localhost:8001/consumers/internal-services/acls \
  -H "Content-Type: application/json" \
  -d '{"group": "service"}' 2>/dev/null || true

echo -e "${GREEN}✓ ACL plugin configured${NC}"

# Step 5: Create JWT generation helper script
cat > generate-jwt.py << 'EOF'
#!/usr/bin/env python3
"""
JWT Token Generator for Kong
Usage: python generate-jwt.py <key> <secret> [expiry_minutes]
"""

import jwt
import sys
import time
from datetime import datetime, timedelta

def generate_token(key, secret, expiry_minutes=60):
    payload = {
        'iss': key,
        'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
        'iat': datetime.utcnow(),
        'nbf': datetime.utcnow()
    }
    
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate-jwt.py <key> <secret> [expiry_minutes]")
        sys.exit(1)
    
    key = sys.argv[1]
    secret = sys.argv[2]
    expiry = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    token = generate_token(key, secret, expiry)
    print(f"JWT Token (expires in {expiry} minutes):")
    print(token)
    print(f"\nUse with: Authorization: Bearer {token}")
EOF

chmod +x generate-jwt.py

# Step 6: Save credentials
cat > jwt-credentials.txt << EOF
JWT Credentials Generated
=========================

Admin User:
-----------
Key: $ADMIN_KEY
Secret: $ADMIN_SECRET
Group: admin

Frontend App:
-------------
Key: $FRONTEND_KEY
Secret: $FRONTEND_SECRET
Group: user

Generate tokens with:
python generate-jwt.py <key> <secret> [expiry_minutes]

Example:
python generate-jwt.py "$ADMIN_KEY" "$ADMIN_SECRET" 60

Test authenticated request:
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/value-models
EOF

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ JWT Authentication Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Credentials saved to: jwt-credentials.txt"
echo ""
echo "Generate a token:"
echo "  python generate-jwt.py \"$ADMIN_KEY\" \"$ADMIN_SECRET\" 60"
echo ""
echo "Test authentication:"
echo '  TOKEN=$(python generate-jwt.py "key" "secret")'
echo '  curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/value-models'
echo ""
