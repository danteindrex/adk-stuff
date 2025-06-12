# Admin Dashboard Integration

## Overview

The admin dashboard has been successfully integrated with authentication and comprehensive metrics for the Uganda E-Gov WhatsApp Helpdesk system.

## Features

### 🔐 Authentication
- **Username**: `trevor`
- **Password**: `The$1000`
- JWT-based authentication with 24-hour token expiration
- Secure session management
- Automatic logout on token expiration

### 📊 Dashboard Metrics
- **Real-time Statistics**:
  - Active user sessions
  - Today's message interactions
  - 24-hour success rate
  - Average response time

- **Service Health Monitoring**:
  - NIRA (Birth Certificates)
  - URA (Tax Services)
  - NSSF (Pension Services)
  - NLIS (Land Records)

- **Language Distribution Chart**:
  - English, Luganda, Luo, Runyoro usage statistics

- **System Logs**:
  - Real-time log streaming
  - Filterable by service
  - Color-coded by log level (info, warning, error)

## API Endpoints

### Authentication
- `POST /admin/login` - Admin login
- `POST /admin/logout` - Admin logout
- `GET /admin/verify` - Verify session

### Dashboard Data
- `GET /admin/dashboard/stats` - Real-time dashboard statistics
- `GET /admin/logs/real-time` - System logs with filtering
- `GET /admin/analytics/usage` - Usage analytics
- `GET /admin/services/health` - Service health status
- `GET /admin/performance/metrics` - Performance metrics
- `GET /admin/alerts` - System alerts
- `POST /admin/alerts/{alert_id}/acknowledge` - Acknowledge alerts
- `GET /admin/users/sessions` - Active user sessions

### System Management
- `POST /admin/system/maintenance` - Toggle maintenance mode

## Access URLs

- **Admin Dashboard**: `http://localhost:8080/admin/`
- **API Documentation**: `http://localhost:8080/docs` (development only)

## Quick Start

1. **Start the server**:
   ```bash
   python start_server.py
   ```

2. **Access the dashboard**:
   - Open browser to `http://localhost:8080/admin/`
   - Login with credentials:
     - Username: `trevor`
     - Password: `The$1000`

3. **Test the API**:
   ```bash
   python test_admin.py
   ```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Session Management**: Active session tracking and cleanup
- **Authorization Headers**: Bearer token authentication for all protected endpoints
- **Automatic Logout**: Sessions expire after 24 hours
- **Failed Login Protection**: Invalid attempts are logged

## Dashboard Features

### Real-time Updates
- Dashboard refreshes every 30 seconds
- Manual refresh button available
- Automatic pause when browser tab is inactive

### Responsive Design
- Mobile-friendly interface
- Adaptive grid layouts
- Touch-friendly controls

### Visual Indicators
- Color-coded service status (green/yellow/red)
- Interactive charts and graphs
- Real-time log streaming

## Technical Implementation

### Backend (FastAPI)
- JWT token generation and validation
- Session management with in-memory store
- Protected route decorators
- Comprehensive error handling
- Structured logging

### Frontend (HTML/CSS/JavaScript)
- Modern responsive design
- Chart.js for data visualization
- Fetch API for backend communication
- Local storage for token persistence
- Automatic authentication handling

### Data Sources
- Mock data for demonstration
- Integration points for real monitoring services
- Extensible architecture for additional metrics

## Monitoring Integration

The dashboard is designed to integrate with:
- System monitoring services
- Database analytics
- Service health checks
- Performance metrics
- Error tracking systems

## Development Notes

### Adding New Metrics
1. Update the `DashboardStats` model in `admin.py`
2. Modify the `get_dashboard_stats` endpoint
3. Update the frontend JavaScript to display new data
4. Add corresponding HTML elements

### Adding New Endpoints
1. Create new route in `admin.py`
2. Add authentication decorator `Depends(verify_admin_token)`
3. Implement business logic
4. Add frontend integration if needed

### Security Considerations
- Tokens are stored in localStorage (consider httpOnly cookies for production)
- Session cleanup on logout
- Rate limiting on authentication endpoints
- HTTPS required for production deployment

## Production Deployment

For production deployment:

1. **Environment Variables**:
   ```bash
   JWT_SECRET_KEY=your-secure-secret-key
   ENVIRONMENT=production
   ```

2. **Security Enhancements**:
   - Use HTTPS
   - Implement rate limiting
   - Add CSRF protection
   - Use secure session storage (Redis)

3. **Monitoring**:
   - Connect to real data sources
   - Set up alerting
   - Configure log aggregation

## Troubleshooting

### Common Issues

1. **Login fails**: Check credentials and server logs
2. **Dashboard not loading**: Verify server is running on port 8080
3. **Token expired**: Automatic redirect to login page
4. **API errors**: Check browser console and server logs

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=debug` in environment variables.

## Support

For issues or questions:
1. Check server logs for error details
2. Verify all dependencies are installed
3. Ensure port 8080 is available
4. Check browser console for frontend errors