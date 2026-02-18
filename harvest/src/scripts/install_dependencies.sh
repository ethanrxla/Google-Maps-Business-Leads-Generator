#!/bin/bash
# Additional dependency installation script

echo "Installing additional tools for enhanced functionality..."

# Install Amass for DNS enumeration
go install -v github.com/OWASP/Amass/v3/...@master

# Install SubFinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install AssetFinder
go install github.com/tomnomnom/assetfinder@latest

# Install HTTPX
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install Naabu
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

echo "Additional tools installed successfully!"