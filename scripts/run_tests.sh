#!/bin/bash

# Uganda E-Gov WhatsApp Helpdesk - Test Runner Script

set -e

echo "🧪 Running Uganda E-Gov WhatsApp Helpdesk Test Suite"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt

# Set test environment variables
export ENVIRONMENT=test
export WHATSAPP_ACCESS_TOKEN=test_token
export WHATSAPP_PHONE_NUMBER_ID=test_phone_id
export WHATSAPP_WEBHOOK_VERIFY_TOKEN=test_verify_token
export WHATSAPP_BUSINESS_ACCOUNT_ID=test_business_id
export GOOGLE_CLOUD_PROJECT=test-project
export FIREBASE_PROJECT_ID=test-firebase-project
export GOOGLE_OAUTH_CLIENT_ID=test_client_id
export GOOGLE_OAUTH_CLIENT_SECRET=test_client_secret
export JWT_SECRET_KEY=test-secret-key-for-testing-purposes-only
export ENCRYPTION_KEY=test-encryption-key-32-characters
export ADMIN_WHATSAPP_GROUP=test_admin_group

# Run different test suites based on arguments
case "${1:-all}" in
    "unit")
        print_status "Running unit tests..."
        pytest tests/test_*.py -v -m "not integration and not performance" --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "integration")
        print_status "Running integration tests..."
        pytest tests/test_integration.py -v --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "performance")
        print_status "Running performance tests..."
        pytest tests/test_performance.py -v -s
        ;;
    "api")
        print_status "Running API tests..."
        pytest tests/test_api.py -v --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "agents")
        print_status "Running agent tests..."
        pytest tests/test_agents.py -v --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "monitoring")
        print_status "Running monitoring tests..."
        pytest tests/test_monitoring.py -v --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "session")
        print_status "Running session manager tests..."
        pytest tests/test_session_manager.py -v --cov=app --cov-report=html --cov-report=term-missing
        ;;
    "all")
        print_status "Running all tests..."
        
        print_status "1. Unit Tests"
        pytest tests/test_*.py -v -m "not performance" --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
        
        print_status "2. Performance Tests (if requested)"
        if [ "${2}" = "with-performance" ]; then
            pytest tests/test_performance.py -v -s
        else
            print_warning "Skipping performance tests (use 'all with-performance' to include them)"
        fi
        ;;
    "quick")
        print_status "Running quick test suite (unit tests only)..."
        pytest tests/test_*.py -v -m "not integration and not performance" --tb=short
        ;;
    *)
        print_error "Unknown test suite: $1"
        echo "Available options:"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  performance  - Run performance tests only"
        echo "  api          - Run API tests only"
        echo "  agents       - Run agent tests only"
        echo "  monitoring   - Run monitoring tests only"
        echo "  session      - Run session manager tests only"
        echo "  all          - Run all tests except performance"
        echo "  all with-performance - Run all tests including performance"
        echo "  quick        - Run quick unit tests only"
        exit 1
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    print_status "✅ All tests passed!"
    
    # Show coverage report location
    if [ -f "htmlcov/index.html" ]; then
        print_status "📊 Coverage report available at: htmlcov/index.html"
    fi
    
    # Show test summary
    echo ""
    echo "📋 Test Summary:"
    echo "==============="
    echo "✅ Tests completed successfully"
    echo "📁 Coverage report: htmlcov/index.html"
    echo "📝 Logs: Check pytest output above"
    
else
    print_error "❌ Some tests failed!"
    exit 1
fi

# Deactivate virtual environment
deactivate

print_status "🎉 Test run completed!"