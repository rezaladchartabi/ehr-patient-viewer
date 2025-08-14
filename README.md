# EHR Patient Viewer

A modern Electronic Health Record (EHR) patient viewer application with FHIR (Fast Healthcare Interoperability Resources) integration. Built with React, TypeScript, and FastAPI.

## Features

- **Patient Management**: View and search patient records with pagination
- **FHIR Integration**: Seamless integration with FHIR-compliant healthcare systems
- **Local Caching**: Intelligent caching system for improved performance
- **Real-time Sync**: Automatic synchronization with remote FHIR servers
- **Responsive UI**: Modern, accessible interface with dark/light theme support
- **Error Handling**: Comprehensive error handling and recovery mechanisms
- **Performance Monitoring**: Built-in performance metrics and monitoring

## Architecture

### Backend (FastAPI)
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLite**: Local database for caching FHIR resources
- **Connection Pooling**: Efficient database connection management
- **Rate Limiting**: Request rate limiting and monitoring
- **Caching**: Multi-level caching system with LRU eviction
- **Error Handling**: Centralized exception handling and logging

### Frontend (React + TypeScript)
- **React 19**: Latest React with concurrent features
- **TypeScript**: Full type safety and better developer experience
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Error Boundaries**: Comprehensive error handling
- **Custom Hooks**: Reusable logic for data fetching and state management

## Prerequisites

- Node.js 18+ and npm 8+
- Python 3.8+
- SQLite 3

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-org/ehr-ui.git
cd ehr-ui
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python init_local_db.py
```

### 3. Frontend Setup
```bash
# Navigate to project root
cd ..

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

### 4. Environment Configuration
Create a `.env.local` file in the project root:
```env
# API Configuration
REACT_APP_API_URL=http://localhost:8005

# Development
REACT_APP_ENV=development
```

**Note**: To change the backend server address, you can either:
1. Update the `REACT_APP_API_URL` in your `.env.local` file
2. Use the provided script: `./scripts/update-backend-url.sh <new-url>`
3. Update the default URL in `src/config.ts`

## Usage

### Development

1. **Start the backend server**:
```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8005 --reload
```

2. **Start the frontend development server**:
```bash
npm start
```

3. **Open your browser** and navigate to `http://localhost:3000`

### Production

1. **Build the frontend**:
```bash
npm run build
```

2. **Start the backend in production mode**:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8005
```

## API Endpoints

### Health and Status
- `GET /` - Health check and system status
- `GET /cache/status` - Cache statistics
- `GET /rate-limit/status` - Rate limiting statistics

### Local Database
- `GET /local/patients` - Get paginated patient list
- `GET /local/patients/{id}` - Get specific patient with allergies
- `GET /local/patients/search` - Search patients

### FHIR Proxy
- `GET /Patient` - FHIR Patient resources
- `GET /Encounter` - FHIR Encounter resources
- `GET /Condition` - FHIR Condition resources
- `GET /AllergyIntolerance` - FHIR Allergy resources

### Encounter Data
- `GET /encounter/medications` - Get medications for encounter
- `GET /encounter/observations` - Get observations for encounter
- `GET /encounter/procedures` - Get procedures for encounter
- `GET /encounter/specimens` - Get specimens for encounter

### Synchronization
- `POST /sync/all` - Sync all FHIR resources
- `POST /sync/patients` - Sync specific patients

## Configuration

### Frontend Configuration
The frontend uses a centralized configuration system. Key files:

- **`src/config.ts`**: Main configuration file with all settings
- **`.env.local`**: Environment-specific configuration (not committed to git)
- **`scripts/update-backend-url.sh`**: Script to update backend URL across the project

#### Changing Backend URL

**Option 1: Environment Variable (Recommended)**
```bash
# Create or update .env.local
echo "REACT_APP_API_URL=https://your-new-backend.com" > .env.local
```

**Option 2: Using the Script**
```bash
# Update URL across all files
./scripts/update-backend-url.sh https://your-new-backend.com
```

**Option 3: Manual Update**
```typescript
// Update src/config.ts
export const config = {
  api: {
    baseUrl: 'https://your-new-backend.com',
    // ... other settings
  }
};
```

### Backend Configuration
The backend uses environment variables for configuration. Key settings:

```env
# FHIR Server
FHIR_BASE_URL=https://imagination-promptly-subsequent-truck.trycloudflare.com/fhir

# Database
DB_PATH=local_ehr.db
DB_MAX_CONNECTIONS=20

# Cache
CACHE_TTL=300
CACHE_MAX_SIZE=2000

# Rate Limiting
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration
Frontend configuration is handled through environment variables:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8005

# Feature Flags
REACT_APP_ENABLE_CACHE=true
REACT_APP_ENABLE_RATE_LIMITING=true
```

## Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest test_main.py

# Run with verbose output
pytest -v
```

### Frontend Tests
```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci
```

## Code Quality

### Backend
```bash
cd backend

# Type checking
mypy .

# Linting
flake8 .

# Format code
black .
```

### Frontend
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check
```

## Performance Monitoring

The application includes built-in performance monitoring:

### Backend Metrics
- Database query performance
- Cache hit/miss rates
- HTTP request statistics
- Rate limiting metrics

### Frontend Metrics
- Bundle size analysis
- Component render performance
- API request timing
- Error tracking

## Error Handling

### Backend Error Handling
- Custom exception classes
- Centralized error handling
- Detailed error logging
- Graceful degradation

### Frontend Error Handling
- Error boundaries for component errors
- API error handling with retry logic
- User-friendly error messages
- Development error details

## Security

- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration
- Secure HTTP headers
- Environment-based configuration

## Deployment

### Docker Deployment
```bash
# Build the image
docker build -t ehr-ui .

# Run the container
docker run -p 8005:8005 ehr-ui
```

### Render Deployment
The application includes `render.yaml` for easy deployment on Render:

```yaml
services:
  - type: web
    name: ehr-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices
- Write comprehensive tests
- Use meaningful commit messages
- Update documentation as needed
- Follow the existing code style

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check if port 8005 is available
   - Verify Python dependencies are installed
   - Check environment variables

2. **Frontend can't connect to backend**
   - Verify backend is running on correct port
   - Check CORS configuration
   - Verify API URL in environment

3. **Database errors**
   - Check database file permissions
   - Verify SQLite is installed
   - Run database initialization script

4. **Performance issues**
   - Check cache configuration
   - Monitor database query performance
   - Verify rate limiting settings

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation

## Acknowledgments

- FHIR community for healthcare standards
- FastAPI team for the excellent web framework
- React team for the amazing frontend library
- All contributors to this project
