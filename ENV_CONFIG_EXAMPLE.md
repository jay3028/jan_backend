# Environment Configuration Example

## Create `.env` File

In the `jansuraksha_backend` directory, create a file named `.env` with the following content:

```bash
# ==================================================
# DATABASE CONFIGURATION
# ==================================================
DATABASE_URL=mysql+pymysql://root:your_password@localhost/jansuraksha_db

# ==================================================
# JWT SECURITY
# ==================================================
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# ==================================================
# FRONTEND CONFIGURATION
# ==================================================
FRONTEND_URL=http://localhost:3000

# ==================================================
# AWS REKOGNITION CONFIGURATION (REQUIRED FOR FACE RECOGNITION)
# ==================================================

# AWS Access Credentials
# Get these from AWS IAM Console after creating a user
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# AWS Region (Mumbai/India = ap-south-1)
# Other options: us-east-1, eu-west-1, etc.
AWS_REGION=ap-south-1

# Rekognition Collection Name
# This is the name of the face collection in AWS Rekognition
# Use different names for dev/staging/prod
REKOGNITION_COLLECTION_ID=jansuraksha-workers

# ==================================================
# OPTIONAL: EMAIL CONFIGURATION
# ==================================================
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# ==================================================
# OPTIONAL: OTHER SERVICES
# ==================================================
# REDIS_URL=redis://localhost:6379/0
# SENTRY_DSN=your-sentry-dsn-for-error-tracking
```

## Important Notes

1. **DO NOT commit `.env` file to version control**
   - The `.env` file contains sensitive credentials
   - It should be in `.gitignore`
   - Each environment (dev/staging/prod) has its own `.env`

2. **AWS Credentials**
   - Replace `AKIAIOSFODNN7EXAMPLE` with your actual Access Key ID
   - Replace the Secret Access Key with your actual key
   - Never share these credentials publicly

3. **Collection ID**
   - Development: `jansuraksha-workers-dev`
   - Staging: `jansuraksha-workers-staging`
   - Production: `jansuraksha-workers-prod`

4. **Security**
   - Change the `SECRET_KEY` to a long random string
   - Use strong database passwords
   - Keep AWS credentials secure

## For Production

In production environments, use environment variables instead of `.env` file:

### Docker Compose

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - SECRET_KEY=${SECRET_KEY}
  - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  - AWS_REGION=ap-south-1
  - REKOGNITION_COLLECTION_ID=jansuraksha-workers-prod
```

### Server (EC2/VPS)

```bash
export DATABASE_URL="mysql+pymysql://user:pass@localhost/db"
export SECRET_KEY="your-secret-key"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="wJalr..."
export AWS_REGION="ap-south-1"
export REKOGNITION_COLLECTION_ID="jansuraksha-workers-prod"
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: jansuraksha-secrets
type: Opaque
stringData:
  database-url: mysql+pymysql://user:pass@localhost/db
  secret-key: your-secret-key
  aws-access-key-id: AKIA...
  aws-secret-access-key: wJalr...
```

## Verification

After creating `.env`, verify it works:

```bash
cd jansuraksha_backend

# Test AWS connection
python -c "from app.services.aws_rekognition import rekognition_service; print('✓ AWS Connected' if rekognition_service.client else '✗ AWS Not Configured')"

# Start server
uvicorn app.main:app --reload
```

Expected output:
```
✓ AWS Rekognition initialized successfully (Region: ap-south-1)
✓ Collection 'jansuraksha-workers' exists
```

## Troubleshooting

### Issue: "AWS Rekognition not configured"

**Check**:
1. `.env` file exists in `jansuraksha_backend` directory
2. AWS credentials are correct (no extra spaces)
3. IAM user has Rekognition permissions
4. Server was restarted after adding credentials

### Issue: "Collection not found"

**Fix**:
The collection will be created automatically on first use. If it fails:
```python
python
>>> from app.services.aws_rekognition import rekognition_service
>>> rekognition_service._ensure_collection_exists()
```

---

For complete setup guide, see: `AWS_REKOGNITION_SETUP_GUIDE.md`

