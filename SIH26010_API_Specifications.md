# SIH26010: Complete API Specifications

## BASE URL
```
Development: http://localhost:5000/api
Production: https://api.sih26010.app/api
```

---

## AUTHENTICATION ENDPOINTS

### 1. User Registration
```
POST /auth/register
Content-Type: application/json

Request:
{
    "email": "farmer@example.com",
    "phone": "9876543210",
    "role": "farmer|surveyor|admin",
    "fullName": "John Doe",
    "password": "SecurePassword123",
    "districtCode": "MH001"
}

Response (201):
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
        "id": 1,
        "email": "farmer@example.com",
        "role": "farmer",
        "createdAt": "2026-09-06T10:30:00Z"
    }
}

Error (400):
{
    "success": false,
    "error": "Email already registered"
}
```

### 2. User Login
```
POST /auth/login
Content-Type: application/json

Request:
{
    "email": "farmer@example.com",
    "password": "SecurePassword123"
}

Response (200):
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
}
```

### 3. Token Refresh
```
POST /auth/refresh
Headers: {
    "Authorization": "Bearer <refreshToken>"
}

Response (200):
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

## SURVEY ENDPOINTS

### 1. Create Survey (Draft)
```
POST /surveys
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

Request:
{
    "plotNumber": "MH-DIST-01-001",
    "ownerName": "Ram Kumar",
    "ownerPhone": "9876543210",
    "village": "Dandegaon",
    "district": "Mumbai",
    "taluka": "Mahape",
    "plotArea": 5000,
    "cropType": "sugarcane",
    "notes": "Located near main road"
}

Response (201):
{
    "success": true,
    "survey": {
        "id": 101,
        "plotNumber": "MH-DIST-01-001",
        "status": "draft",
        "createdAt": "2026-09-06T10:30:00Z",
        "syncRequired": false
    }
}
```

### 2. Add GPS Boundary to Survey
```
POST /surveys/:surveyId/gps-boundary
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

Request:
{
    "gpsPoints": [
        {
            "latitude": 19.1136,
            "longitude": 72.8697,
            "accuracy": 5.2,
            "timestamp": 1694007600000,
            "altitude": 15.5
        },
        {
            "latitude": 19.1140,
            "longitude": 72.8700,
            "accuracy": 4.8,
            "timestamp": 1694007605000,
            "altitude": 15.6
        }
        // ... minimum 3 points required
    ]
}

Response (200):
{
    "success": true,
    "boundary": {
        "surveyId": 101,
        "pointCount": 45,
        "areaCalculated": 5015,
        "geoJSON": {
            "type": "Polygon",
            "coordinates": [...]
        },
        "boundaryQuality": "Good"
    }
}
```

### 3. Upload Survey Image
```
POST /surveys/:surveyId/images
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "multipart/form-data"
}

Form Data:
- image: <binary image file>
- imageType: "drone|ground|boundary|other"
- caption: "North boundary view"
- latitude: 19.1136
- longitude: 72.8697

Response (201):
{
    "success": true,
    "image": {
        "id": 1,
        "surveyId": 101,
        "imageType": "ground",
        "url": "https://cdn.sih26010.app/images/survey-101-img-1.jpg",
        "uploadedAt": "2026-09-06T10:35:00Z"
    }
}
```

### 4. Submit Survey for Review
```
PUT /surveys/:surveyId/submit
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

Request:
{
    "surveyorNotes": "Survey completed successfully. Boundary verified by 3-point check.",
    "qualityRating": 4.5,
    "completionPercentage": 100
}

Response (200):
{
    "success": true,
    "survey": {
        "id": 101,
        "status": "submitted",
        "submittedAt": "2026-09-06T11:00:00Z",
        "assignedReviewer": "Officer-M001"
    }
}
```

### 5. Get Survey Details
```
GET /surveys/:surveyId
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "survey": {
        "id": 101,
        "plotNumber": "MH-DIST-01-001",
        "owner": {
            "id": 5,
            "name": "Ram Kumar",
            "phone": "9876543210"
        },
        "status": "submitted",
        "gpsData": {
            "points": 45,
            "accuracy": "±5.2m",
            "boundary": "GeoJSON..."
        },
        "images": [
            {
                "id": 1,
                "type": "ground",
                "url": "https://...",
                "uploadedAt": "2026-09-06T10:35:00Z"
            }
        ],
        "createdAt": "2026-09-06T10:30:00Z",
        "updatedAt": "2026-09-06T11:00:00Z"
    }
}
```

### 6. Get User's Surveys
```
GET /surveys?status=draft&limit=20&offset=0
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "surveys": [
        {
            "id": 101,
            "plotNumber": "MH-DIST-01-001",
            "status": "draft",
            "lastUpdated": "2026-09-06T10:35:00Z"
        },
        {
            "id": 102,
            "plotNumber": "MH-DIST-01-002",
            "status": "submitted",
            "lastUpdated": "2026-09-06T11:00:00Z"
        }
    ],
    "pagination": {
        "total": 45,
        "limit": 20,
        "offset": 0
    }
}
```

---

## LAND RECORD ENDPOINTS

### 1. Generate Land Record
```
POST /land-records/generate
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

Request:
{
    "surveyId": 101,
    "includeDocumentation": true,
    "format": "pdf|json|both"
}

Response (201):
{
    "success": true,
    "record": {
        "recordId": "LR-MH-DIST-01-001-2026",
        "surveyId": 101,
        "plotNumber": "MH-DIST-01-001",
        "owner": "Ram Kumar",
        "area": {
            "sqMeters": 5015,
            "hectares": 0.5015,
            "acres": 1.24
        },
        "boundary": "GeoJSON...",
        "generatedAt": "2026-09-06T11:30:00Z",
        "documentUrl": "https://cdn.sih26010.app/records/LR-MH-DIST-01-001-2026.pdf",
        "status": "pending_approval"
    }
}
```

### 2. Get Land Record
```
GET /land-records/:recordId
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "record": {
        "recordId": "LR-MH-DIST-01-001-2026",
        "owner": {
            "name": "Ram Kumar",
            "phone": "9876543210",
            "aadhar": "****7890"  // Masked
        },
        "plotData": {
            "plotNumber": "MH-DIST-01-001",
            "area": 5015,
            "boundary": "GeoJSON...",
            "cropType": "sugarcane"
        },
        "verificationData": {
            "gpsAccuracy": "±5.2m",
            "aiConfidence": 0.92,
            "surveyorName": "Officer-M001",
            "surveyDate": "2026-09-06",
            "approvalStatus": "pending"
        },
        "documentHash": "sha256:abc123...",
        "createdAt": "2026-09-06T11:30:00Z"
    }
}
```

### 3. Approve/Reject Land Record
```
PUT /land-records/:recordId/approve
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json",
    "X-Role": "admin|reviewer"
}

Request:
{
    "action": "approve|reject",
    "comments": "All verification checks passed",
    "officerId": "OFFICER-001"
}

Response (200):
{
    "success": true,
    "record": {
        "recordId": "LR-MH-DIST-01-001-2026",
        "status": "approved",
        "approvedAt": "2026-09-06T12:00:00Z",
        "approvedBy": "Officer-M001"
    }
}
```

---

## OFFLINE SYNC ENDPOINTS

### 1. Sync Offline Data
```
POST /sync/offline-surveys
Headers: {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

Request:
{
    "surveys": [
        {
            "id": "local_1694007600000",
            "plotNumber": "MH-DIST-01-001",
            "gpsPoints": [...],
            "images": [
                {
                    "uri": "file:///...",
                    "type": "ground"
                }
            ],
            "createdAt": 1694007600000
        }
    ]
}

Response (200):
{
    "success": true,
    "synced": 1,
    "failed": 0,
    "results": [
        {
            "localId": "local_1694007600000",
            "serverId": 101,
            "status": "synced"
        }
    ]
}
```

### 2. Get Pending Syncs
```
GET /sync/pending
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "pending": [
        {
            "id": "local_1694007600000",
            "type": "survey",
            "plotNumber": "MH-DIST-01-001",
            "lastAttempt": "2026-09-06T09:00:00Z",
            "attempts": 2
        }
    ]
}
```

---

## DASHBOARD & ANALYTICS ENDPOINTS

### 1. Dashboard Statistics
```
GET /dashboard/stats?period=month
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "stats": {
        "totalSurveys": 1250,
        "completedSurveys": 980,
        "areaCovered": 1250.5,  // hectares
        "averageAccuracy": 4.8,  // meters
        "totalUsers": 45,
        "activeSurveyors": 32,
        "pendingApprovals": 15
    }
}
```

### 2. District-wise Summary
```
GET /analytics/district-summary
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "districts": [
        {
            "districtCode": "MH001",
            "districtName": "Mumbai",
            "surveysCompleted": 150,
            "areaSurveyed": 250.5,
            "avgAccuracy": 4.9,
            "activeOfficers": 8
        }
    ]
}
```

### 3. Quality Metrics
```
GET /analytics/quality-metrics
Headers: {
    "Authorization": "Bearer <token>"
}

Response (200):
{
    "success": true,
    "metrics": {
        "gpsAccuracyAvg": 4.8,
        "aiConfidenceAvg": 0.89,
        "recordApprovalRate": 0.94,
        "surveyCompletionTime": 18.5,  // minutes
        "imageQualityScore": 0.88,
        "errorRate": 0.02
    }
}
```

---

## ERROR RESPONSES

### Standard Error Format
```
{
    "success": false,
    "error": "Error message",
    "code": "ERROR_CODE",
    "details": {
        "field": "plotNumber",
        "issue": "Field is required"
    }
}
```

### Common Error Codes
- `INVALID_TOKEN`: 401 - Token expired or invalid
- `UNAUTHORIZED`: 403 - User doesn't have permission
- `NOT_FOUND`: 404 - Resource not found
- `VALIDATION_ERROR`: 400 - Input validation failed
- `CONFLICT`: 409 - Resource already exists
- `SERVER_ERROR`: 500 - Internal server error
- `SERVICE_UNAVAILABLE`: 503 - Service temporarily down
- `OFFLINE_QUEUE_FULL`: 429 - Too many offline requests

---

## RATE LIMITING

```
- Public endpoints: 100 requests/hour
- Authenticated endpoints: 1000 requests/hour
- Upload endpoints: 50 requests/hour
- Sync endpoints: Unlimited (priority)

Headers in Response:
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1694010600
```

---

## WEBSOCKET EVENTS (Real-time Updates)

### Connect
```javascript
socket.emit('connect', { token: '<auth-token>' });
```

### Listen for Real-time Events
```javascript
// Survey submission
socket.on('survey:submitted', (data) => {
    // { surveyId, surveyorId, plotNumber, timestamp }
});

// Survey approved
socket.on('survey:approved', (data) => {
    // { recordId, approverName, timestamp }
});

// Offline sync started
socket.on('sync:started', (data) => {
    // { surveyCount, totalSize }
});

// Offline sync progress
socket.on('sync:progress', (data) => {
    // { completed, total, percentage }
});

// Offline sync completed
socket.on('sync:completed', (data) => {
    // { synced, failed, errors }
});
```

---

## PAGINATION

All list endpoints support:
```
GET /surveys?limit=20&offset=0&sort=createdAt&order=desc
```

Response includes:
```json
{
    "data": [...],
    "pagination": {
        "total": 1250,
        "limit": 20,
        "offset": 0,
        "hasMore": true
    }
}
```

---

## CONTENT TYPES ACCEPTED
- `application/json`
- `multipart/form-data` (for file uploads)
- `application/x-www-form-urlencoded`

## CORS HEADERS
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

