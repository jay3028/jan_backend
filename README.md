# Jan Suraksha Backend

National Last-Mile Trust & Verification Platform - Backend API

## Team - Wavelet Tree

**Team Members:**
- **Abhinav Rai** - Rajiv Gandhi Institute Of Petroleum Technology
- **Kunal Kumar** - Rajiv Gandhi Institute Of Petroleum Technology
- **Jay Kumar** - Rajiv Gandhi Institute Of Petroleum Technology

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file with the following variables:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/jansuraksha_db
JWT_SECRET=your-secret-key-change-in-production
SECRET_KEY=your-secret-key

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Jan Suraksha

# AWS Configuration (for Face Verification)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

### 3. Initialize Database

```bash
# Create tables
python init_db.py

# Create tables and admin user
python init_db.py --with-admin
```

Default admin credentials:
- Email: admin@jansuraksha.gov.in
- Password: admin123
- **⚠️ CHANGE THIS IMMEDIATELY!**

### 4. Run Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## API Documentation

Once the server is running, access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Architecture

### User Roles
- **Worker**: Delivery workers and AePS agents
- **Company**: Service providers who employ workers
- **Police**: Law enforcement for verification
- **Admin**: Platform administrators

### Key Features

1. **Authentication**
   - Email + Password
   - Mobile + OTP
   - JWT-based sessions
   - Role-based access control

2. **Worker Onboarding**
   - Multi-step form (6 steps)
   - Auto-save progress
   - Selfie capture
   - Aadhaar reference (token only)
   - Device fingerprinting

3. **Police Verification**
   - Face verification (AWS Rekognition)
   - 1:1 face matching
   - Liveness detection
   - Certificate upload
   - Verification status tracking

4. **Worker ID Generation**
   - Format: IND-WRK-{CATEGORY}-YYYY-XXXXXX
   - QR code generation
   - Public verification endpoint

5. **Company Management**
   - Worker linking
   - Status management (Active/Inactive/Suspended)
   - Complaint submission
   - API key authentication

6. **Risk Management**
   - Complaint tracking
   - Risk score calculation
   - Blacklist management
   - Incident logging

7. **Public Verification**
   - QR code scanning
   - Worker ID lookup
   - Mobile number search
   - Limited public data exposure

8. **Audit & Compliance**
   - Complete audit trail
   - All actions logged
   - Admin oversight
   - ICJS-aligned messaging

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/request-otp` - Request OTP
- `POST /api/auth/verify-otp` - Verify OTP
- `GET /api/auth/me` - Get current user

### Workers
- `POST /api/workers/onboard/step1-6` - Onboarding steps
- `GET /api/workers/me` - Get worker profile
- `GET /api/workers/onboarding/status` - Get onboarding progress

### Companies
- `POST /api/companies/register` - Register company
- `POST /api/companies/workers/{worker_id}/link` - Link worker
- `GET /api/companies/workers` - Get linked workers
- `POST /api/companies/complaints` - Submit complaint

### Police
- `GET /api/police/verification-queue` - Get pending verifications
- `POST /api/police/verify-face` - Face verification
- `POST /api/police/verify` - Create verification
- `POST /api/police/incident` - Log incident
- `POST /api/police/suspend` - Suspend worker

### Verification (Public)
- `POST /api/verify/worker` - Verify worker (public)
- `GET /api/verify/worker/{worker_id}` - Verify by ID (public)

### Admin
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/users` - List users
- `GET /api/admin/workers` - List workers
- `POST /api/admin/companies/{id}/approve` - Approve company
- `GET /api/admin/audit-logs` - View audit logs
- `POST /api/admin/blacklist/{worker_id}` - Blacklist worker

## Security Features

- JWT-based authentication
- Password hashing (bcrypt)
- OTP verification for email/mobile
- Role-based access control
- API key authentication for companies
- Device fingerprinting
- Audit logging
- No raw Aadhaar storage
- Limited public data exposure

## Database Schema

See `app/models.py` for complete schema including:
- Users
- Workers
- Companies
- Police Officers
- Police Verifications
- Complaints
- Incidents
- Audit Logs

## Development

```bash
# Run tests (TODO)
pytest

# Code formatting
black app/

# Type checking
mypy app/
```

## Production Deployment

1. Set proper environment variables
2. Use production database
3. Configure HTTPS
4. Set up proper CORS origins
5. Use production-grade WSGI server
6. Set up monitoring and logging
7. Regular backups
8. Security hardening

