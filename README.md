# EHR Patient Viewer System

A comprehensive Electronic Health Record (EHR) system built with React and FastAPI, designed to display and manage patient data from MIMIC-IV datasets.

## 🏥 Features

- **Complete Patient Data View**: Display all patient information including demographics, conditions, medications, encounters, and more
- **Multi-Data Type Support**: 
  - Patients (20 records)
  - Conditions (1,320 records)
  - Medications (3,603 records)
  - Encounters (179 records)
  - Medication Administrations (16,367 records)
  - Medication Requests (4,656 records)
  - Observations (81,868 records)
  - Procedures (714 records)
  - Specimens (3,585 records)
- **Modern UI**: Clean, responsive interface with tabbed navigation
- **Real-time Data**: Live API integration with comprehensive backend
- **Search & Filter**: Easy patient selection and data browsing

## 🚀 Quick Start

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8+
- Git

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ehr-ui
```

2. **Install dependencies**
```bash
npm install
```

3. **Start the development server**
```bash
npm start
```

4. **Start the backend API** (in a separate terminal)
```bash
cd backend
pip install -r requirements.txt
python main.py
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8002

## 📊 Data Overview

The system includes comprehensive MIMIC-IV data:

| Data Type | Records | Description |
|-----------|---------|-------------|
| Patients | 20 | Patient demographics and basic info |
| Conditions | 1,320 | Medical conditions and diagnoses |
| Medications | 3,603 | Prescribed medications |
| Encounters | 179 | Hospital visits and encounters |
| Med Admin | 16,367 | Medication administration records |
| Med Requests | 4,656 | Medication prescription requests |
| Observations | 81,868 | Lab results and clinical observations |
| Procedures | 714 | Medical procedures performed |
| Specimens | 3,585 | Lab specimens collected |

## 🏗️ Architecture

### Frontend (React)
- **Framework**: React 18 with TypeScript
- **Styling**: Inline styles with modern CSS Grid/Flexbox
- **State Management**: React Hooks (useState, useEffect)
- **API Integration**: Fetch API for backend communication

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.11
- **Database**: SQLite with comprehensive schema
- **API**: RESTful endpoints for all data types
- **CORS**: Configured for cross-origin requests

### Database Schema
- **Patient**: Core patient information
- **Condition**: Medical conditions and diagnoses
- **Medication**: Prescribed medications
- **Encounter**: Hospital visits and encounters
- **Medication_Administration**: Medication administration records
- **Medication_Request**: Medication prescription requests
- **Observation**: Lab results and clinical observations
- **Procedure**: Medical procedures
- **Specimen**: Lab specimens

## 🌐 Deployment

### Quick Deployment
Run the deployment script:
```bash
./deploy.sh
```

### Manual Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

### Recommended Platforms
- **Free**: Render, Railway, Netlify, Vercel
- **Paid**: DigitalOcean, Heroku, AWS

## 🔧 Configuration

### Environment Variables
- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8002)

### API Endpoints
- `GET /patients` - List all patients
- `GET /patients/{id}` - Get specific patient
- `GET /patients/{id}/summary` - Patient dashboard
- `GET /patients/{id}/{data-type}` - Patient-specific data
- `GET /{data-type}` - List all records of a type

## 🔒 Security

For production deployment:
1. Add authentication to the API
2. Restrict CORS origins
3. Use environment variables for sensitive data
4. Implement rate limiting
5. Add HTTPS encryption

## 📱 Usage

1. **Select a Patient**: Click on any patient from the left sidebar
2. **View Summary**: See the patient overview with data counts
3. **Explore Data**: Use the tabs to navigate between different data types
4. **Browse Records**: View detailed information for each record type

## 🛠️ Development

### Project Structure
```
ehr-ui/
├── src/
│   ├── App.tsx          # Main application component
│   ├── index.tsx        # Application entry point
│   └── ...
├── backend/
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── ehr_data.sqlite3 # Database file
├── public/              # Static assets
├── package.json         # Node.js dependencies
└── README.md           # This file
```

### Adding New Features
1. **New Data Type**: Add interface, state, and API calls in App.tsx
2. **New Endpoint**: Add route in backend/main.py
3. **UI Enhancement**: Modify components in src/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please ensure compliance with data privacy regulations when using with real patient data.

## 🆘 Support

For issues and questions:
1. Check the deployment logs
2. Verify environment variables
3. Test API endpoints directly
4. Review browser console for errors

## 🎯 Roadmap

- [ ] Add authentication system
- [ ] Implement search and filtering
- [ ] Add data visualization charts
- [ ] Create mobile-responsive design
- [ ] Add data export functionality
- [ ] Implement real-time updates
- [ ] Add audit logging
- [ ] Create admin dashboard

---

**Built with ❤️ for healthcare professionals**
