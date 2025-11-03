"""
Setup script for Windows EFIS Data Manager Service.
"""

from setuptools import setup, find_packages

setup(
    name="efis-data-manager-windows",
    version="1.0.0",
    description="Windows service component for EFIS Data Manager",
    author="EFIS Data Manager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pywin32>=306",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "psutil>=5.9.6",
        "watchdog>=3.0.0",
        "colorlog>=6.8.0"
    ],
    entry_points={
        "console_scripts": [
            "efis-windows-service=efis_windows.service:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)