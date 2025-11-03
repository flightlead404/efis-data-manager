"""Setup script for EFIS Data Manager."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Platform-specific requirements
windows_requirements = [
    "pywin32>=306",
    "psutil>=5.9.0",
]

macos_requirements = [
    "pync>=2.0.3",
    "plyer>=2.1.0",
]

# Common requirements
common_requirements = [
    "requests>=2.28.0",
    "beautifulsoup4>=4.11.0",
    "lxml>=4.9.0",
    "watchdog>=2.1.0",
    "paramiko>=2.11.0",
    "cryptography>=37.0.0",
    "pyyaml>=6.0",
    "jsonschema>=4.0.0",
]

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
    "mypy>=0.991",
]

setup(
    name="efis-data-manager",
    version="1.0.0",
    author="EFIS Data Manager Team",
    description="Cross-platform aviation chart and EFIS data management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=common_requirements,
    extras_require={
        "windows": windows_requirements,
        "macos": macos_requirements,
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "efis-windows-service=windows.service:main",
            "efis-macos-daemon=macos.daemon:main",
            "efis-cli=shared.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
)