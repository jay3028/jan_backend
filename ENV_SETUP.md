# Environment Variables Setup

## Create .env file

Create a `.env` file in the `jansuraksha_backend` directory with these variables:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/jansuraksha_db

# Frontend URL (for QR code generation)
# IMPORTANT: QR codes will redirect to this URL
FRONTEND_URL=http://localhost:3000

# Backend URL (for API endpoints)
BACKEND_URL=http://localhost:8000

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## For Development (Current Setup)

```bash
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

**QR Code will contain:** `http://localhost:3000/verify?id=IND-WRK-DLV-2025-958738`

## For Production

```bash
FRONTEND_URL=https://jansuraksha.gov.in
BACKEND_URL=https://api.jansuraksha.gov.in
```

**QR Code will contain:** `https://jansuraksha.gov.in/verify?id=IND-WRK-DLV-2025-958738`

## Important Notes

1. **QR codes are permanent** - Once generated, they contain the URL from when they were created
2. **Regenerate QR codes** when changing from development to production
3. **Use consistent URLs** - Both worker and police see the same QR code from database
4. **Restart backend** after changing .env variables

## How to Apply Changes

1. Update `.env` file
2. Restart backend:
   ```bash
   cd jansuraksha_backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Regenerate QR codes for existing workers (via UI or migration script)

