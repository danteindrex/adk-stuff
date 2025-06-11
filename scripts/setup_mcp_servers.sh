#!/bin/bash

# Uganda E-Gov WhatsApp Helpdesk - MCP Servers Setup Script
# This script sets up all required MCP servers for the application

set -e

echo "🚀 Setting up MCP Servers for Uganda E-Gov WhatsApp Helpdesk..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js is installed: $NODE_VERSION"
    else
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    print_status "Checking npm installation..."
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm is installed: $NPM_VERSION"
    else
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python is installed: $PYTHON_VERSION"
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip installation..."
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
        print_success "pip is installed: $PIP_VERSION"
    else
        print_error "pip is not installed. Please install pip first."
        exit 1
    fi
}

# Install Playwright MCP Server
install_playwright_mcp() {
    print_status "Installing Playwright MCP Server..."
    
    # Install globally to make it available for the application
    if npm list -g @microsoft/playwright-mcp &> /dev/null; then
        print_warning "Playwright MCP Server is already installed"
    else
        npm install -g @microsoft/playwright-mcp@latest
        print_success "Playwright MCP Server installed successfully"
    fi
    
    # Install Playwright browsers
    print_status "Installing Playwright browsers..."
    npx playwright install
    print_success "Playwright browsers installed successfully"
}

# Install WhatsApp MCP Server
install_whatsapp_mcp() {
    print_status "Installing WhatsApp MCP Server..."
    
    if npm list -g @lharries/whatsapp-mcp &> /dev/null; then
        print_warning "WhatsApp MCP Server is already installed"
    else
        npm install -g @lharries/whatsapp-mcp@latest
        print_success "WhatsApp MCP Server installed successfully"
    fi
}

# Install Browser-Use Python package
install_browser_use() {
    print_status "Installing Browser-Use Python package..."
    
    if pip3 show browser-use &> /dev/null; then
        print_warning "Browser-Use is already installed"
    else
        pip3 install browser-use
        print_success "Browser-Use installed successfully"
    fi
}

# Install additional Python dependencies
install_python_deps() {
    print_status "Installing additional Python dependencies..."
    
    # Install from requirements.txt if it exists
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_success "Python dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found, installing core dependencies..."
        pip3 install playwright aiohttp requests
        print_success "Core Python dependencies installed"
    fi
}

# Create MCP server configuration
create_mcp_config() {
    print_status "Creating MCP server configuration..."
    
    # Create logs directory for browser-use
    mkdir -p logs/browser_use
    print_success "Created logs directory for browser-use"
    
    # Create MCP server configuration file
    cat > mcp_servers.json << EOF
{
    "servers": {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@microsoft/playwright-mcp@latest"],
            "description": "Playwright browser automation MCP server"
        },
        "whatsapp": {
            "command": "npx", 
            "args": ["-y", "@lharries/whatsapp-mcp@latest"],
            "description": "WhatsApp Business API MCP server"
        }
    },
    "python_tools": {
        "browser_use": {
            "package": "browser-use",
            "description": "AI-powered browser automation fallback"
        }
    }
}
EOF
    print_success "MCP server configuration created"
}

# Test MCP servers
test_mcp_servers() {
    print_status "Testing MCP servers..."
    
    # Test Playwright MCP
    print_status "Testing Playwright MCP server..."
    if timeout 10s npx @microsoft/playwright-mcp@latest --help &> /dev/null; then
        print_success "Playwright MCP server is working"
    else
        print_warning "Playwright MCP server test failed or timed out"
    fi
    
    # Test WhatsApp MCP
    print_status "Testing WhatsApp MCP server..."
    if timeout 10s npx @lharries/whatsapp-mcp@latest --help &> /dev/null; then
        print_success "WhatsApp MCP server is working"
    else
        print_warning "WhatsApp MCP server test failed or timed out"
    fi
    
    # Test Browser-Use
    print_status "Testing Browser-Use..."
    if python3 -c "import browser_use; print('Browser-Use imported successfully')" &> /dev/null; then
        print_success "Browser-Use is working"
    else
        print_warning "Browser-Use test failed"
    fi
}

# Main setup function
main() {
    echo "=================================================="
    echo "🇺🇬 Uganda E-Gov WhatsApp Helpdesk MCP Setup"
    echo "=================================================="
    echo ""
    
    # Check prerequisites
    check_nodejs
    check_npm
    check_python
    check_pip
    
    echo ""
    print_status "Installing MCP servers and dependencies..."
    echo ""
    
    # Install MCP servers
    install_playwright_mcp
    install_whatsapp_mcp
    install_browser_use
    install_python_deps
    
    echo ""
    print_status "Configuring MCP servers..."
    echo ""
    
    # Create configuration
    create_mcp_config
    
    echo ""
    print_status "Testing MCP servers..."
    echo ""
    
    # Test installations
    test_mcp_servers
    
    echo ""
    echo "=================================================="
    print_success "MCP Servers setup completed successfully!"
    echo "=================================================="
    echo ""
    echo "📋 Summary of installed components:"
    echo "   ✅ Playwright MCP Server (@microsoft/playwright-mcp)"
    echo "   ✅ WhatsApp MCP Server (@lharries/whatsapp-mcp)"
    echo "   ✅ Browser-Use Python package (browser-use)"
    echo "   ✅ Playwright browsers"
    echo "   ✅ MCP server configuration (mcp_servers.json)"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Copy .env.production.template to .env"
    echo "   2. Fill in your WhatsApp Business API credentials"
    echo "   3. Set your security keys (JWT_SECRET_KEY, ENCRYPTION_KEY)"
    echo "   4. Start the application with: python main.py"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
}

# Run main function
main "$@"