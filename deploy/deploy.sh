#!/bin/bash

# Root-MAS Deployment Script
# This script automates the deployment of Root-MAS on a remote server

set -e  # Exit on any error

# Configuration
PROJECT_NAME="root-mas"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/opt/backups/${PROJECT_NAME}"
LOG_FILE="/var/log/${PROJECT_NAME}_deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
    fi
}

# Install Docker and Docker Compose if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    else
        info "Docker is already installed"
    fi

    if ! command -v docker-compose &> /dev/null; then
        log "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        info "Docker Compose is already installed"
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/opt/${PROJECT_NAME}"
    mkdir -p "/var/log"
}

# Backup existing deployment
backup_existing() {
    if [ -d "/opt/${PROJECT_NAME}" ] && [ "$(ls -A /opt/${PROJECT_NAME})" ]; then
        log "Backing up existing deployment..."
        BACKUP_NAME="${PROJECT_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "/opt/${PROJECT_NAME}" "${BACKUP_DIR}/${BACKUP_NAME}"
        log "Backup saved to ${BACKUP_DIR}/${BACKUP_NAME}"
    fi
}

# Deploy the application
deploy_application() {
    log "Deploying Root-MAS application..."
    
    cd "/opt/${PROJECT_NAME}"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warning ".env file not found. Please create it with your API keys and configuration."
        info "You can copy .env.example as a template."
        return 1
    fi
    
    # Pull latest images and deploy
    log "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    log "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    
    log "Starting new deployment..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check if containers are running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        log "Containers are running successfully"
    else
        error "Some containers failed to start"
    fi
    
    # Check Prometheus metrics endpoint
    if curl -s http://localhost:9000/metrics > /dev/null; then
        log "Prometheus metrics endpoint is accessible"
    else
        warning "Prometheus metrics endpoint is not accessible"
    fi
    
    # Check if Prometheus is running
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        log "Prometheus is healthy"
    else
        warning "Prometheus health check failed"
    fi
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    cat > "/etc/logrotate.d/${PROJECT_NAME}" << EOF
$LOG_FILE {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
}

# Setup systemd service for automatic startup
setup_systemd_service() {
    log "Setting up systemd service..."
    cat > "/etc/systemd/system/${PROJECT_NAME}.service" << EOF
[Unit]
Description=Root-MAS Multi-Agent System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${PROJECT_NAME}
ExecStart=/usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} up -d
ExecStop=/usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${PROJECT_NAME}.service"
    log "Systemd service created and enabled"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo "===================="
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    echo ""
    echo "Access URLs:"
    echo "- Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
    echo "- Metrics: http://$(hostname -I | awk '{print $1}'):9000/metrics"
    echo "- Application: http://$(hostname -I | awk '{print $1}'):8000 (when implemented)"
    echo ""
    echo "Logs location: $LOG_FILE"
    echo "Backup location: $BACKUP_DIR"
}

# Main deployment function
main() {
    log "Starting Root-MAS deployment..."
    
    check_privileges
    create_directories
    install_docker
    backup_existing
    
    # Copy project files if not already there
    if [ ! -f "/opt/${PROJECT_NAME}/docker-compose.prod.yml" ]; then
        info "Project files not found in /opt/${PROJECT_NAME}. Please copy them manually."
        info "You can use: rsync -av /path/to/project/ /opt/${PROJECT_NAME}/"
        exit 1
    fi
    
    deploy_application
    setup_log_rotation
    setup_systemd_service
    
    log "Deployment completed successfully!"
    show_status
}

# Handle script arguments
case "${1:-}" in
    "deploy")
        main
        ;;
    "status")
        cd "/opt/${PROJECT_NAME}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        ;;
    "logs")
        cd "/opt/${PROJECT_NAME}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "stop")
        cd "/opt/${PROJECT_NAME}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        ;;
    "restart")
        cd "/opt/${PROJECT_NAME}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" restart "${2:-}"
        ;;
    "backup")
        backup_existing
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|stop|restart|backup}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment process"
        echo "  status  - Show service status"
        echo "  logs    - Show logs (optional service name)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart services (optional service name)"
        echo "  backup  - Backup current deployment"
        exit 1
        ;;
esac