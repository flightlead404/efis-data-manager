"""
Setup script for macOS EFIS Data Manager Daemon.
"""

from setuptools import setup, find_packages

setup(
    name="efis-data-manager-macos",
    version="1.0.0",
    description="macOS daemon component for EFIS Data Manager",
    author="EFIS Data Manager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "psutil>=5.9.6",
        "watchdog>=3.0.0",
        "colorlog>=6.8.0"
    ],
    entry_points={
        "console_scripts": [
            "efis-macos-daemon=efis_macos.daemon:main",
            "efis-daemon-manager=daemon_manager:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)