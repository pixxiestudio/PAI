#!/bin/bash
# Generate secrets for GitHub Actions deployment
# Usage: ./generate-secrets.sh

set -e

echo "🔐 GitHub Actions Secrets Generator"
echo "===================================="
echo ""

# Generate JWT_SECRET
echo "1️⃣  JWT_SECRET (for backend token signing)"
JWT_SECRET=$(openssl rand -hex 16)
echo "   Value: $JWT_SECRET"
echo "   ✅ Copy this to GitHub secret: JWT_SECRET"
echo ""

# Generate ENCRYPTION_KEY for credential encryption
echo "2️⃣  ENCRYPTION_KEY (for credential encryption)"
# Need Fernet-compatible key (base64)
if command -v python3 &> /dev/null; then
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "   Value: $ENCRYPTION_KEY"
    echo "   ✅ Copy this to backend .env: ENCRYPTION_KEY"
else
    # Fallback
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    echo "   Value: $ENCRYPTION_KEY"
    echo "   ⚠️  Note: This may not be Fernet-compatible. Use Python-generated key if possible."
fi
echo ""

# Display other secrets needed
echo "3️⃣  Other Required Secrets"
echo "   ANTHROPIC_API_KEY:"
echo "      • Get from: https://console.anthropic.com/account/keys"
echo "      • Starts with: sk-ant-"
echo ""
echo "   GCP_SA_KEY:"
echo "      • Get from: Google Cloud Console → Service Accounts"
echo "      • Format: JSON key file (copy entire content)"
echo ""
echo "   GCP_PROJECT_ID:"
echo "      • Get from: Google Cloud Console (top bar)"
echo "      • Example: my-pai-project-12345"
echo ""
echo "   VERCEL_TOKEN:"
echo "      • Get from: https://vercel.com/account/tokens"
echo "      • Starts with: vercel_"
echo ""
echo "   VERCEL_ORG_ID:"
echo "      • Get from: https://vercel.com/account/settings"
echo "      • Look for Team ID"
echo ""
echo "   GITHUB_TOKEN:"
echo "      • Get from: GitHub Settings → Developer settings → Personal access tokens"
echo "      • Starts with: ghp_"
echo ""

echo "📋 Summary"
echo "=========="
echo "Save these values:"
echo ""
echo "JWT_SECRET=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo ""

# Ask if user wants to save to .env
read -p "Save JWT_SECRET and ENCRYPTION_KEY to .env.local? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f .env.local ]; then
        echo "JWT_SECRET=$JWT_SECRET" >> .env.local
        echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env.local
        echo "✅ Saved to .env.local"
    else
        cat > .env.local << EOF
# Generated secrets
JWT_SECRET=$JWT_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
EOF
        echo "✅ Created .env.local with secrets"
    fi
else
    echo "⏭️  Skipped saving to file"
fi

echo ""
echo "🚀 Next Steps:"
echo "1. Add all 7 secrets to GitHub (Settings → Secrets and variables → Actions)"
echo "2. Use the secrets guide: docs/github-secrets-guide.md"
echo "3. Commit changes and push to trigger CI/CD"
