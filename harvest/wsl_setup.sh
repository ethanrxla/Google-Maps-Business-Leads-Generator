#!/bin/bash
# wsl_setup.sh - Setup theHarvester automation in WSL

echo "Setting up theHarvester automation in WSL..."

# Update Kali
sudo apt update && sudo apt upgrade -y

# Install required dependencies
sudo apt install -y python3-pip git seclists

# Install theHarvester (if not already installed)
if ! command -v theHarvester &> /dev/null; then
    echo "Installing theHarvester..."
    sudo pip3 install theharvester
fi

# Create project directory
mkdir -p ~/harvester_automation
cd ~/harvester_automation

# Create Windows accessible symlink
ln -sf $(pwd) /mnt/c/Users/$USER/harvester_automation

echo "Setup complete!"
echo "Project directory: ~/harvester_automation"
echo "Windows access: C:\\Users\\$USER\\harvester_automation"