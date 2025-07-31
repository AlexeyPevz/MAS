#!/usr/bin/env python3
# Simple installer for AI Memory System
import os
import sys
import subprocess
from pathlib import Path

print('AI Memory System - Simple Installer')
print('=' * 40)

# Базовая установка
install_path = input('Installation path [~/ai-memory-system]: ').strip()
if not install_path:
    install_path = str(Path.home() / 'ai-memory-system')

print(f'Installing to: {install_path}')
Path(install_path).mkdir(parents=True, exist_ok=True)

print('Installation complete!')
print(f'System installed to: {install_path}')
