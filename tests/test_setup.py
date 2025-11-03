"""
Test script to verify project setup is working correctly.
Tests configuration loading and logging setup.
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_configuration_loading():
    """Test that configuration can be loaded successfully."""
    try:
        from shared.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config_file = project_root / 'config' / 'efis_config.yaml'
        
        if not config_file.exists():
            print(f"❌ Configuration file not found: {config_file}")
            return False
            
        config.load_config(str(config_file))
        
        # Test required configuration keys
        required_keys = [
            'windows.virtualDriveFile',
            'windows.driveLetter',
            'macos.archivePath',
            'logging.maxBytes'
        ]
        
        for key in required_keys:
            value = config.get(key)
            if value is None:
                print(f"❌ Missing required configuration key: {key}")
                return False
            print(f"✅ {key}: {value}")
            
        print("✅ Configuration loading test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False


def test_logging_setup():
    """Test that logging can be set up successfully."""
    try:
        from shared.utils.logging_config import setup_component_logging
        
        # Test configuration
        config = {
            'logging': {
                'logLevel': 'INFO',
                'maxBytes': 1024 * 1024,
                'backupCount': 3
            }
        }
        
        # Set up logging for test component
        logger = setup_component_logging('test', config, str(project_root / 'tests'))
        
        # Test logging at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        print("✅ Logging setup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Logging setup test failed: {e}")
        return False


def test_data_models():
    """Test that data models can be imported and used."""
    try:
        from shared.models.data_models import (
            FileMetadata, SyncResult, EFISDrive, 
            OperationStatus, DriveStatus
        )
        from datetime import datetime
        
        # Test FileMetadata
        file_meta = FileMetadata(
            path="/test/file.txt",
            size=1024,
            hash="abc123",
            last_modified=datetime.now()
        )
        print(f"✅ FileMetadata created: {file_meta.path}")
        
        # Test SyncResult
        sync_result = SyncResult(
            status=OperationStatus.SUCCESS,
            files_transferred=5,
            bytes_transferred=5120
        )
        print(f"✅ SyncResult created: {sync_result.status}")
        
        # Test EFISDrive
        efis_drive = EFISDrive(
            mount_path="/Volumes/EFIS",
            identifier="EFIS_DRIVE",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        print(f"✅ EFISDrive created: {efis_drive.identifier}")
        
        print("✅ Data models test passed")
        return True
        
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False


def main():
    """Run all setup tests."""
    print("🔧 Testing EFIS Data Manager project setup...\n")
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Logging Setup", test_logging_setup),
        ("Data Models", test_data_models)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test:")
        if test_func():
            passed += 1
        
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All setup tests passed! Project structure is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the setup.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)