#!/usr/bin/env python3
"""
WSL integration utilities
"""

import os
import subprocess
import platform
from typing import Optional, Dict, Any

class WSLEnvironment:
    def __init__(self):
        self.wsl_version = self.detect_wsl_version()
        self.windows_hostname = self.get_windows_hostname()
        self.windows_username = self.get_windows_username()
        self.available_drives = self.get_windows_drives()
    
    def detect_wsl_version(self) -> str:
        """Detect WSL version"""
        try:
            with open('/proc/version', 'r') as f:
                content = f.read().lower()
                if 'microsoft' in content:
                    if 'wsl2' in content:
                        return 'WSL2'
                    else:
                        return 'WSL1'
        except:
            pass
        
        # Check for Windows directory
        if os.path.exists('/mnt/c/Windows'):
            return 'WSL (Unknown Version)'
        
        return 'Native Linux'
    
    def get_windows_hostname(self) -> str:
        """Get Windows hostname"""
        try:
            result = subprocess.run(
                ['cmd.exe', '/c', 'hostname'],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else 'Unknown'
        except:
            return 'Unknown'
    
    def get_windows_username(self) -> str:
        """Get current Windows username"""
        try:
            result = subprocess.run(
                ['cmd.exe', '/c', 'echo %USERNAME%'],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else 'UnknownUser'
        except:
            return 'UnknownUser'
    
    def get_windows_drives(self) -> List[str]:
        """Get available Windows drives"""
        drives = []
        for drive in ['c', 'd', 'e', 'f', 'g']:
            if os.path.exists(f'/mnt/{drive}'):
                drives.append(drive)
        return drives
    
    def convert_wsl_to_windows_path(self, wsl_path: str) -> Optional[str]:
        """Convert WSL path to Windows path"""
        try:
            result = subprocess.run(
                ['wslpath', '-w', wsl_path],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def convert_windows_to_wsl_path(self, windows_path: str) -> Optional[str]:
        """Convert Windows path to WSL path"""
        try:
            result = subprocess.run(
                ['wslpath', '-u', windows_path],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def open_in_windows_explorer(self, path: str) -> bool:
        """Open path in Windows Explorer"""
        try:
            windows_path = self.convert_wsl_to_windows_path(path)
            if windows_path:
                subprocess.run(['explorer.exe', windows_path], timeout=10)
                return True
        except:
            pass
        return False