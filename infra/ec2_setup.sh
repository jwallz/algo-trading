#!/bin/bash
# EC2 setup script for algo trading instance
# Target: Ubuntu 22.04 LTS on t3.medium
# Run as: bash ec2_setup.sh

set -e

echo "=== Updating system ==="
sudo apt-get update && sudo apt-get upgrade -y

echo "=== Installing dependencies ==="
sudo apt-get install -y \
    git \
    curl \
    unzip \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    docker.io \
    docker-compose

echo "=== Configuring Docker ==="
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

echo "=== Installing AWS CLI ==="
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

echo "=== Cloning repo ==="
# Update this URL after repo is set up
# git clone https://github.com/jwallz/algo-trading.git ~/algo-trading

echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Log out and back in for Docker group to take effect"
echo "  2. Run: cd ~/algo-trading/infra && docker-compose up -d"
echo "  3. Configure AWS credentials: aws configure"
