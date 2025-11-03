# EFIS Data Manager Testing Framework

This directory contains comprehensive tests for the EFIS Data Manager project, covering unit tests, integration tests, and end-to-end validation scenarios.

## Test Structure

```
tests/
├── shared/                 # Tests for shared components
│   ├── test_config_manager.py
│   └── test_data_models.py
├── windows/               # Tests for Windows-specific components
│   ├── test_imdisk_wrapper.py
│   └── test_sync_engine.py
├── macos/                 # Tests for macOS-specific components
│   ├── test_grt_scraper_unit.py
│   └── test_usb_drive_processor_unit.py
├── integration/           # Integration and end-to-end tests
│   ├── test_end_to_end_workflow.py
│   ├── test_network_failure_simulation.py
│   ├── test_usb_drive_lifecycle.py
│   └── test_performance_load.py
└── test_setup.py         # Project setup validation
```

## Test Categories

### Unit Tests
Focus on testing individual components and functions in isolation:

- **Configuration Management**: Config loading, validation, and access
- **Data Models**: Core data structures and their behavior
- **ImDisk Wrapper**: Windows virtual drive management
- **Sync Engine**: File synchronization algorithms
- **GRT Scraper**: Web scraping and version detection
- **USB Drive Processor**: Drive detection and file processing

### Integration Tests
Test component interactions and complete workflows:

- **End-to-End Workflows**: Complete USB drive processing, chart synchronization
- **Network Failure Simulation**: Connectivity issues, retry mechanisms, graceful degradation
- **USB Drive Lifecycle**: Drive insertion, processing, updating, ejection
- **Performance and Load**: Scalability, memory usage, concurrent operations

## Running Tests

### Quick Start
```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --existing
python run_tests.py --setup
```

### Using pytest directly
```bash
# Run unit tests
pytest tests/shared/ tests/windows/ tests/macos/ -v

# Run integration tests
pytest tests/integration/ -v -s

# Run specific test file
pytest tests/shared/test_config_manager.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Requirements

### Dependencies
```bash
pip install pytest pytest-cov
```

### Optional Dependencies (for full functionality)
```bash
pip install psutil requests beautifulsoup4 lxml pyyaml
```

## Test Design Principles

### Unit Tests
- **Isolation**: Each test is independent and doesn't rely on external systems
- **Mocking**: External dependencies are mocked to ensure predictable behavior
- **Fast Execution**: Unit tests should complete quickly (< 1 second each)
- **Comprehensive Coverage**: Test both success and failure scenarios

### Integration Tests
- **Real Interactions**: Test actual component interactions where possible
- **Simulation**: Use simulators for external systems (USB drives, network)
- **Error Scenarios**: Test error handling and recovery mechanisms
- **Performance**: Validate system behavior under load

## Key Test Features

### Network Simulation
The `NetworkSimulator` class provides:
- Connectivity on/off simulation
- Latency and packet loss simulation
- Bandwidth throttling
- Connection recovery testing

### USB Drive Simulation
The `USBDriveSimulator` class provides:
- Drive insertion/removal events
- Different drive types (EFIS, regular, empty)
- File system simulation
- Error condition simulation

### Performance Testing
The `PerformanceTestSuite` class provides:
- Operation timing measurement
- Memory usage tracking
- Scalability analysis
- Stress testing capabilities

## Test Data and Fixtures

### Temporary Directories
All tests use temporary directories that are automatically cleaned up:
```python
def setup_method(self):
    self.temp_dir = tempfile.mkdtemp()

def teardown_method(self):
    shutil.rmtree(self.temp_dir, ignore_errors=True)
```

### Mock Data
Tests create realistic mock data:
- EFIS drive content (demo files, snapshots, logbooks)
- Chart data structures
- Configuration files
- Network responses

## Continuous Integration

### GitHub Actions (Future)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --all
```

## Test Coverage Goals

- **Unit Tests**: > 80% code coverage
- **Integration Tests**: All major workflows covered
- **Error Scenarios**: All error paths tested
- **Performance**: Baseline performance metrics established

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import Mock, patch

class TestMyComponent:
    def setup_method(self):
        """Set up test fixtures."""
        self.component = MyComponent()
    
    def test_basic_functionality(self):
        """Test basic component functionality."""
        result = self.component.do_something()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(MyException):
            self.component.do_invalid_operation()
```

### Integration Test Template
```python
import tempfile
from pathlib import Path

class TestMyIntegration:
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Create test data
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_workflow(self):
        """Test complete workflow."""
        # Set up scenario
        # Execute workflow
        # Verify results
        pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **Permission Errors**: Tests may fail on read-only file systems
3. **Timeout Errors**: Integration tests may timeout on slow systems
4. **Missing Dependencies**: Some tests require optional dependencies

### Debug Mode
```bash
# Run with verbose output
pytest -v -s

# Run single test with debugging
pytest tests/shared/test_config_manager.py::TestConfigManager::test_load_config_success -v -s
```

## Performance Benchmarks

### Expected Performance (on modern hardware)
- Unit tests: < 30 seconds total
- Integration tests: < 2 minutes total
- Memory usage: < 100MB peak
- File operations: > 10MB/s throughput

## Contributing

When adding new functionality:
1. Write unit tests for new components
2. Add integration tests for new workflows
3. Update this README if adding new test categories
4. Ensure all tests pass before submitting PR

## Test Results Interpretation

### Success Indicators
- ✅ All tests pass
- 🎉 Performance within expected ranges
- 📊 Good test coverage

### Warning Indicators
- ⚠️ Some optional tests skipped (missing dependencies)
- ⏰ Tests taking longer than expected
- 📈 Memory usage higher than baseline

### Failure Indicators
- ❌ Test failures
- 💥 Unexpected errors
- 🔥 Performance degradation