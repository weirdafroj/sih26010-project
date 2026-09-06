# SIH26010: Rural Agricultural Land Survey Digitization
## Complete Implementation Guide from Scratch

---

## PART 1: SYSTEM ARCHITECTURE OVERVIEW

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Services (AWS/GCP)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Gateway | Authentication | Land Records DB       │   │
│  │ AI Processing | Drone Image Storage | Analytics       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────┬───────────────────┘
         │                              │
    ┌────▼──────────┐          ┌────────▼──────┐
    │  Mobile App   │          │   Web Portal   │
    │  (Farmers &   │          │   (Officers &  │
    │  Officers)    │          │   Admin)       │
    │               │          │                │
    │ GPS/Mapping   │          │ Dashboard      │
    │ Offline Mode  │          │ Reports        │
    └────┬──────────┘          └────────┬───────┘
         │                              │
    ┌────▼──────────────────────────────▼───┐
    │    Cloud Sync & Data Aggregation      │
    │  (When connectivity returns)           │
    └───────────────────────────────────────┘
```

---

## PART 2: TECHNOLOGY STACK RECOMMENDATIONS

### Backend (Server-Side)
- **Runtime**: Node.js + Express OR Django/Python
- **Database**: PostgreSQL (with PostGIS for geospatial data)
- **Cache**: Redis (for offline sync queue)
- **Message Queue**: RabbitMQ or Kafka (for async processing)
- **APIs**: RESTful + WebSockets (for real-time updates)

### Mobile App
- **Frontend**: React Native or Flutter (cross-platform)
- **Offline Storage**: SQLite or Realm Database
- **Maps**: Google Maps SDK + Mapbox (for offline tiles)
- **GPS**: Native GPS APIs + accurate positioning libraries
- **Sync Engine**: Custom sync engine (detects connectivity changes)

### Web Portal
- **Frontend**: React.js or Vue.js
- **Maps Visualization**: Leaflet.js + GeoJSON rendering
- **State Management**: Redux/Vuex
- **Charts**: Chart.js or D3.js for analytics

### AI/ML Components
- **Image Processing**: Python + OpenCV, Rasterio
- **Land Detection**: TensorFlow/PyTorch trained models
- **Drone Integration**: DroneDB or DJI SDK
- **Map Generation**: GDAL, GeoServer

### Infrastructure
- **Deployment**: Docker + Kubernetes
- **CDN**: CloudFlare for static assets
- **Storage**: S3-compatible storage for drone images
- **Monitoring**: Prometheus + Grafana

---

## PART 3: PROJECT PHASES & MILESTONES

### Phase 1: Foundation (Weeks 1-2)
**Duration**: 10 days | **Team Size**: 4-5 people

#### 1.1 Backend Setup
```bash
# Initialize project
mkdir sih26010-backend
cd sih26010-backend
npm init -y
npm install express dotenv cors axios multer

# Directory structure
sih26010-backend/
├── server.js
├── .env
├── routes/
│   ├── auth.js
│   ├── survey.js
│   └── lands.js
├── controllers/
│   ├── surveyController.js
│   └── landController.js
├── middleware/
│   ├── auth.js
│   └── errorHandler.js
├── models/
│   ├── User.js
│   ├── Survey.js
│   └── LandPlot.js
└── config/
    └── database.js
```

**Key Tasks**:
- Set up Express server with basic routes
- Connect to PostgreSQL database
- Create authentication system (JWT tokens)
- Design database schema for users, surveys, land plots

#### 1.2 Database Schema (PostgreSQL)
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15),
    role ENUM('farmer', 'surveyor', 'admin'),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Land Plots table
CREATE TABLE land_plots (
    id SERIAL PRIMARY KEY,
    plot_number VARCHAR(50) UNIQUE,
    owner_id INTEGER REFERENCES users(id),
    village VARCHAR(100),
    district VARCHAR(100),
    area_sq_meters DECIMAL(15,2),
    gps_coordinates GEOMETRY(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Surveys table
CREATE TABLE surveys (
    id SERIAL PRIMARY KEY,
    plot_id INTEGER REFERENCES land_plots(id),
    surveyor_id INTEGER REFERENCES users(id),
    survey_date TIMESTAMP,
    gps_points GEOMETRY(LineString, 4326),
    status ENUM('draft', 'submitted', 'approved'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Survey Images table
CREATE TABLE survey_images (
    id SERIAL PRIMARY KEY,
    survey_id INTEGER REFERENCES surveys(id),
    image_url VARCHAR(255),
    image_type ENUM('drone', 'ground', 'boundary'),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.3 Authentication & Authorization
```javascript
// routes/auth.js
const express = require('express');
const jwt = require('jsonwebtoken');
const router = express.Router();

router.post('/register', async (req, res) => {
    const { email, phone, role, password } = req.body;
    // Hash password, save to DB, return JWT
    const token = jwt.sign({ userId, role }, process.env.JWT_SECRET);
    res.json({ token });
});

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    // Verify credentials, return JWT
    const token = jwt.sign({ userId, role }, process.env.JWT_SECRET);
    res.json({ token });
});

module.exports = router;
```

---

### Phase 2: Mobile App Development (Weeks 3-4)
**Duration**: 12 days | **Team Size**: 3-4 people

#### 2.1 Project Setup (React Native + Expo)
```bash
npx create-expo-app sih26010-mobile
cd sih26010-mobile
npm install react-native-maps react-native-geolocation-service
npm install @react-native-async-storage/async-storage
npm install axios
npm install expo-camera expo-media-library
```

#### 2.2 Core Modules

**A. GPS & Location Tracking**
```javascript
// src/services/gpsService.js
import * as Location from 'expo-location';

export const startGPSTracking = async (callback) => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return;
    
    Location.watchPositionAsync(
        {
            accuracy: Location.Accuracy.BestForNavigation,
            timeInterval: 5000,
            distanceInterval: 10
        },
        (location) => {
            callback({
                latitude: location.coords.latitude,
                longitude: location.coords.longitude,
                accuracy: location.coords.accuracy,
                timestamp: Date.now()
            });
        }
    );
};

export const getGPSBoundary = (gpsPoints) => {
    // Convert array of GPS points to polygon boundary
    return gpsPoints.map(p => [p.latitude, p.longitude]);
};
```

**B. Offline Storage & Sync**
```javascript
// src/services/offlineService.js
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

export const saveOfflineSurvey = async (surveyData) => {
    const key = `survey_${Date.now()}`;
    await AsyncStorage.setItem(key, JSON.stringify({
        ...surveyData,
        synced: false,
        createdAt: Date.now()
    }));
};

export const syncOfflineData = async (api) => {
    const state = await NetInfo.fetch();
    
    if (state.isConnected) {
        const keys = await AsyncStorage.getAllKeys();
        const surveyKeys = keys.filter(k => k.startsWith('survey_'));
        
        for (const key of surveyKeys) {
            const data = await AsyncStorage.getItem(key);
            try {
                await api.post('/surveys', JSON.parse(data));
                await AsyncStorage.removeItem(key);
            } catch (err) {
                console.log('Sync failed, will retry later');
            }
        }
    }
};
```

**C. Map Interface**
```javascript
// src/screens/SurveyMapScreen.js
import MapView, { Polygon, Marker } from 'react-native-maps';
import { useState, useEffect } from 'react';
import { View, Button } from 'react-native';

export default function SurveyMapScreen() {
    const [gpsPoints, setGpsPoints] = useState([]);
    const [isRecording, setIsRecording] = useState(false);

    useEffect(() => {
        if (isRecording) {
            startGPSTracking((location) => {
                setGpsPoints(prev => [...prev, location]);
            });
        }
    }, [isRecording]);

    return (
        <View style={{ flex: 1 }}>
            <MapView
                style={{ flex: 1 }}
                initialRegion={{
                    latitude: 20.5937,
                    longitude: 78.9629,
                    latitudeDelta: 0.05,
                    longitudeDelta: 0.05
                }}
            >
                {gpsPoints.length > 2 && (
                    <Polygon
                        coordinates={gpsPoints.map(p => ({
                            latitude: p.latitude,
                            longitude: p.longitude
                        }))}
                        fillColor="rgba(0, 200, 0, 0.3)"
                        strokeColor="#00c800"
                        strokeWidth={2}
                    />
                )}
                
                {gpsPoints.map((point, i) => (
                    <Marker key={i} coordinate={point} />
                ))}
            </MapView>
            
            <Button
                title={isRecording ? "Stop Recording" : "Start Recording"}
                onPress={() => setIsRecording(!isRecording)}
            />
        </View>
    );
}
```

**D. Camera & Image Capture**
```javascript
// src/services/cameraService.js
import * as ImagePicker from 'expo-image-picker';

export const captureImage = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    
    if (status !== 'granted') return null;
    
    const result = await ImagePicker.launchCameraAsync({
        allowsEditing: false,
        aspect: [4, 3],
        quality: 0.8
    });
    
    return result.assets[0];
};

export const uploadImage = async (imageUri, surveyId, api) => {
    const formData = new FormData();
    formData.append('image', {
        uri: imageUri,
        name: `survey_${surveyId}.jpg`,
        type: 'image/jpeg'
    });
    formData.append('surveyId', surveyId);
    
    return api.post('/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
};
```

---

### Phase 3: Web Portal Development (Weeks 3-4)
**Duration**: 12 days | **Team Size**: 2-3 people

#### 3.1 React Setup
```bash
npx create-react-app sih26010-web
cd sih26010-web
npm install leaflet react-leaflet axios recharts
npm install @react-leaflet/core
```

#### 3.2 Admin Dashboard
```javascript
// src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import axios from 'axios';

export default function Dashboard() {
    const [surveys, setSurveys] = useState([]);
    const [stats, setStats] = useState({});

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const response = await axios.get('/api/dashboard/stats', {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            setStats(response.data);
            
            const surveysResponse = await axios.get('/api/surveys', {
                headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
            });
            setSurveys(surveysResponse.data);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        }
    };

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            {/* Sidebar Stats */}
            <div style={{ width: '20%', padding: '20px', backgroundColor: '#f5f5f5' }}>
                <h2>Survey Statistics</h2>
                <p>Total Surveys: {stats.totalSurveys}</p>
                <p>Approved: {stats.approvedSurveys}</p>
                <p>Pending: {stats.pendingSurveys}</p>
                <p>Area Covered: {stats.areaCovered} sq.km</p>
            </div>

            {/* Map */}
            <div style={{ flex: 1 }}>
                <MapContainer center={[20.5937, 78.9629]} zoom={5} style={{ height: '100%' }}>
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; OpenStreetMap contributors'
                    />
                    {surveys.map(survey => (
                        <GeoJSON key={survey.id} data={survey.geoJSON} />
                    ))}
                </MapContainer>
            </div>
        </div>
    );
}
```

---

### Phase 4: AI/ML Integration (Weeks 4-5)
**Duration**: 10 days | **Team Size**: 2-3 people

#### 4.1 Drone Image Processing
```python
# backend/ai_service/land_detection.py
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import rasterio
from shapely.geometry import shape

class LandBoundaryDetector:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        
    def process_drone_image(self, image_path):
        """
        Process drone image and detect land boundaries
        """
        # Read image
        with rasterio.open(image_path) as src:
            image = src.read()
        
        # Preprocess
        image = cv2.resize(image, (512, 512))
        image = image / 255.0
        
        # Predict boundaries
        mask = self.model.predict(np.expand_dims(image, 0))[0]
        
        # Convert to GeoJSON polygon
        contours, _ = cv2.findContours(
            (mask > 0.5).astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        polygons = []
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # Filter small noise
                coords = contour.squeeze().tolist()
                if len(coords) >= 3:
                    polygons.append(coords)
        
        return polygons
    
    def merge_gps_and_imagery(self, gps_points, image_polygons, georef_data):
        """
        Combine GPS traced boundary with AI-detected imagery boundaries
        """
        # Weight GPS data more heavily for accuracy
        combined = {
            'gps_boundary': gps_points,
            'ai_detected': image_polygons,
            'confidence': self.calculate_confidence(gps_points, image_polygons),
            'georeferenced': True
        }
        return combined

# Usage in backend
detector = LandBoundaryDetector('models/land_boundary_model.h5')
```

#### 4.2 Drone Integration (Using DJI SDK or similar)
```python
# backend/drone_service/flight_control.py
from dji_sdk import Aircraft, FlightController
import time

class DroneFlightPlanner:
    def __init__(self, aircraft_model='Phantom 4'):
        self.aircraft = Aircraft(aircraft_model)
    
    def plan_survey_flight(self, land_plot_boundary, overlap=80, altitude=100):
        """
        Generate waypoints for automatic drone survey flight
        """
        # Convert land boundary to flight path
        waypoints = self.generate_grid_waypoints(
            boundary=land_plot_boundary,
            overlap_percent=overlap,
            flight_altitude=altitude
        )
        
        # Create mission
        mission = {
            'waypoints': waypoints,
            'camera_settings': {
                'interval': 2,  # Photo every 2 seconds
                'resolution': 'max'
            },
            'return_to_home': True
        }
        
        return mission
    
    def execute_mission(self, mission):
        """Execute automated survey flight"""
        self.aircraft.start_mission(mission)
```

---

## PART 4: KEY FEATURES IMPLEMENTATION

### Feature 1: Offline-First Survey Creation
```javascript
// Mobile App: Survey Form with Offline Support
export const SurveyForm = () => {
    const [formData, setFormData] = useState({
        plotNumber: '',
        ownerName: '',
        area: '',
        gpsPoints: [],
        images: [],
        notes: ''
    });
    
    const [isOnline, setIsOnline] = useState(true);

    const handleSave = async () => {
        // Always save locally first
        await saveOfflineSurvey(formData);
        
        if (isOnline) {
            // Try to sync immediately if connected
            await syncOfflineData(apiClient);
        } else {
            alert('Survey saved offline. Will sync when connected.');
        }
    };

    return (
        <View>
            <Text>Connectivity: {isOnline ? 'Online' : 'Offline'}</Text>
            {/* Form fields */}
            <Button title="Save Survey" onPress={handleSave} />
        </View>
    );
};
```

### Feature 2: Auto-Generate Land Records
```python
# Backend: Digital Land Record Generation
class LandRecordGenerator:
    def generate_record(self, survey_data):
        """Generate official digital land record"""
        record = {
            'record_id': self.generate_unique_id(),
            'plot_data': {
                'plot_number': survey_data['plotNumber'],
                'owner': survey_data['owner'],
                'area': survey_data['area'],
                'boundaries': survey_data['gps_boundary'],
                'survey_date': datetime.now().isoformat()
            },
            'verification': {
                'gps_accuracy': survey_data['gps_accuracy_meters'],
                'imagery_confidence': survey_data['ai_confidence'],
                'surveyor_id': survey_data['surveyor_id'],
                'status': 'pending_approval'
            },
            'legal': {
                'document_hash': self.create_hash(survey_data),
                'blockchain_tx': None  # Optional: blockchain storage
            }
        }
        
        return self.save_to_database(record)
```

### Feature 3: Real-time Officer Dashboard
```javascript
// Web App: Real-time Survey Tracking
import io from 'socket.io-client';

export const OfficerDashboard = () => {
    const [liveUpdates, setLiveUpdates] = useState([]);

    useEffect(() => {
        const socket = io(process.env.REACT_APP_API_URL);
        
        socket.on('survey_started', (data) => {
            setLiveUpdates(prev => [...prev, {
                ...data,
                status: 'in_progress',
                timestamp: new Date()
            }]);
        });
        
        socket.on('survey_completed', (data) => {
            setLiveUpdates(prev => 
                prev.map(s => s.id === data.id ? {...s, status: 'completed'} : s)
            );
        });
        
        return () => socket.disconnect();
    }, []);

    return (
        <div>
            <h2>Live Survey Updates</h2>
            <table>
                <thead>
                    <tr>
                        <th>Surveyor</th>
                        <th>Plot</th>
                        <th>Status</th>
                        <th>Progress</th>
                    </tr>
                </thead>
                <tbody>
                    {liveUpdates.map(update => (
                        <tr key={update.id}>
                            <td>{update.surveyorName}</td>
                            <td>{update.plotNumber}</td>
                            <td>{update.status}</td>
                            <td>{update.completionPercent}%</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
```

---

## PART 5: DEPLOYMENT & DEVOPS

### Docker Setup
```dockerfile
# Dockerfile for backend
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 5000
CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgres://user:pass@db:5432/sih26010
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - db
      - redis

  db:
    image: postgis/postgis:latest
    environment:
      POSTGRES_DB: sih26010
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: ./web
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Deployment Steps (AWS/GCP)
```bash
# 1. Push to Docker Registry
docker tag sih26010-backend:latest gcr.io/project-id/sih26010-backend:latest
docker push gcr.io/project-id/sih26010-backend:latest

# 2. Deploy to Kubernetes
kubectl apply -f k8s/
kubectl rollout status deployment/sih26010-backend

# 3. Set up CI/CD
# .github/workflows/deploy.yml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm test
      - run: docker build -t sih26010 .
      - run: kubectl apply -f k8s/
```

---

## PART 6: TESTING STRATEGY

### Unit Tests (Backend)
```javascript
// tests/survey.test.js
const request = require('supertest');
const app = require('../server');

describe('Survey API', () => {
    it('should create a new survey', async () => {
        const response = await request(app)
            .post('/api/surveys')
            .set('Authorization', `Bearer ${token}`)
            .send({
                plotNumber: 'TEST001',
                gpsPoints: [[20.5, 78.9], [20.51, 78.91]],
                area: 5000
            });
        
        expect(response.status).toBe(201);
        expect(response.body.id).toBeDefined();
    });
});
```

### Integration Tests
```python
# tests/integration/test_land_detection.py
import pytest
from ai_service.land_detection import LandBoundaryDetector

@pytest.fixture
def detector():
    return LandBoundaryDetector('models/test_model.h5')

def test_process_drone_image(detector, sample_image):
    result = detector.process_drone_image(sample_image)
    assert len(result) > 0
    assert 'polygons' in result
```

---

## PART 7: TIMELINE & DELIVERABLES

```
Week 1-2: Backend & Database
  ✓ API structure
  ✓ Authentication
  ✓ Database schema
  ✓ Basic CRUD operations

Week 3-4: Mobile App
  ✓ GPS tracking
  ✓ Offline storage
  ✓ Map interface
  ✓ Image capture
  ✓ Sync engine

Week 3-4: Web Portal (Parallel)
  ✓ Dashboard
  ✓ Map visualization
  ✓ Reporting
  ✓ User management

Week 4-5: AI/ML
  ✓ Image processing
  ✓ Boundary detection
  ✓ GPS-imagery fusion
  ✓ Model optimization

Week 5-6: Integration & Testing
  ✓ End-to-end testing
  ✓ Performance optimization
  ✓ Security audit
  ✓ Pilot testing

Week 6-7: Deployment & Documentation
  ✓ Dockerization
  ✓ Cloud deployment
  ✓ User documentation
  ✓ Training materials
```

---

## PART 8: CRITICAL CHALLENGES & SOLUTIONS

### Challenge 1: Poor Internet Connectivity in Rural Areas
**Solution**: 
- Full offline capability with auto-sync
- Data compression for large image files
- Differential sync (only changed data)
- Background sync service on app

### Challenge 2: GPS Accuracy Variations
**Solution**:
- Multi-point averaging
- Sensor fusion (GPS + accelerometer + compass)
- Confidence scoring for each point
- Manual correction interface for officers

### Challenge 3: Drone Image Georeferencing
**Solution**:
- Extract metadata from drone sensors
- Use ground control points
- AI-based image registration
- Manual verification by surveyor

### Challenge 4: Data Security & Integrity
**Solution**:
- Encrypted local storage
- HTTPS for all communications
- Digital signatures on records
- Optional blockchain hashing
- Role-based access control

### Challenge 5: Scalability for Millions of Land Plots
**Solution**:
- Microservices architecture
- Horizontal scaling with Kubernetes
- Database sharding by district/region
- Caching strategies (Redis)
- Async processing for heavy workloads

---

## PART 9: RESOURCE REQUIREMENTS

### Development Team (9-12 people)
- 1 Project Manager
- 2 Backend Developers
- 2 Mobile Developers
- 2 Frontend Developers
- 1 ML/AI Engineer
- 1 DevOps Engineer
- 1 QA Engineer
- 1 UI/UX Designer

### Infrastructure (AWS/GCP)
- Cloud compute (4-8 VMs)
- PostgreSQL managed database
- Object storage (S3)
- CDN services
- Estimated monthly cost: $2,000-5,000

### Tools & Licenses
- IDE: VSCode (Free)
- Mapping: Mapbox or Google Maps API
- Project Management: Jira, Notion
- Version Control: GitHub

---

## PART 10: SUCCESS METRICS

### Technical KPIs
- Survey creation time: < 15 minutes per plot
- GPS accuracy: ± 5 meters
- Image processing time: < 2 minutes per image
- System uptime: 99.5%
- Sync success rate: 99%+
- App load time: < 3 seconds

### Business KPIs
- Land plots surveyed: 10,000+ in pilot phase
- User adoption: 80%+ adoption among target users
- Cost reduction: 60% reduction vs. manual survey
- Record accuracy: 95%+ accuracy validation
- Government integration: Successful data sharing

---

## QUICK START CHECKLIST

- [ ] Set up Git repository and team access
- [ ] Configure development environment (Node.js, Python, React)
- [ ] Create AWS/GCP project and configure resources
- [ ] Initialize backend with Express/Django
- [ ] Set up PostgreSQL with PostGIS
- [ ] Create mobile app skeleton (React Native/Flutter)
- [ ] Build React web app structure
- [ ] Implement authentication
- [ ] Set up CI/CD pipeline
- [ ] Begin phase 1 development
- [ ] Weekly sync meetings with stakeholders
- [ ] Document all API endpoints (Swagger/OpenAPI)
- [ ] Create user testing plan
- [ ] Plan pilot deployment strategy

