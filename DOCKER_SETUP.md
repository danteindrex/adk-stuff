# Docker Setup Guide for WSL

## Issue: Docker Permission Denied

The error you encountered is common in WSL environments:
```
permission denied while trying to connect to the Docker daemon socket
```

## Solutions

### Option 1: Install Docker Desktop (Recommended)

1. **Download Docker Desktop for Windows**
   - Go to https://www.docker.com/products/docker-desktop/
   - Download and install Docker Desktop

2. **Enable WSL 2 Integration**
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration with your WSL distribution (Ubuntu-24.04)
   - Click "Apply & Restart"

3. **Test Docker**
   ```bash
   docker --version
   docker run hello-world
   ```

### Option 2: Install Docker Engine in WSL

1. **Update package index**
   ```bash
   sudo apt update
   ```

2. **Install Docker**
   ```bash
   # Install required packages
   sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

   # Add Docker's official GPG key
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

   # Add Docker repository
   echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

   # Install Docker Engine
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io
   ```

3. **Add user to docker group**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. **Start Docker service**
   ```bash
   sudo service docker start
   ```

### Option 3: Use Docker without sudo (if Docker is installed)

If Docker is already installed but you're getting permission errors:

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Test Docker
docker --version
```

## Building the Project

Once Docker is working, you can build the project:

```bash
# Build production image
docker build -f Dockerfile.prod -t uganda-egov-helpdesk .

# Run the container
docker run -d \
  --name uganda-egov-helpdesk \
  --env-file .env \
  -p 8080:8080 \
  uganda-egov-helpdesk

# Or use docker-compose
docker-compose up -d
```

## Alternative: Run Without Docker

If you prefer not to use Docker, you can run the application directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Setup MCP servers
./scripts/setup_mcp_servers.sh

# Start Redis
redis-server &

# Start the application
python main.py
```

## Troubleshooting

### Docker Desktop Issues
- Ensure WSL 2 is enabled in Windows features
- Restart Docker Desktop after enabling WSL integration
- Check that virtualization is enabled in BIOS

### Permission Issues
- Make sure your user is in the docker group
- Restart your terminal session after adding to docker group
- Try `sudo docker` as a temporary workaround

### WSL Issues
- Update WSL: `wsl --update`
- Restart WSL: `wsl --shutdown` then reopen terminal
- Check WSL version: `wsl -l -v`

## Next Steps

After Docker is working:
1. Build the project: `docker build -f Dockerfile.prod -t uganda-egov-helpdesk .`
2. Configure environment variables in `.env`
3. Run the application: `docker-compose up -d`
4. Test the health endpoint: `curl http://localhost:8080/health`