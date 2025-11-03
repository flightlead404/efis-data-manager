"""
Integration tests for performance and load testing scenarios.
"""

import pytest
import tempfile
import time
import threading
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch


class PerformanceTestSuite:
    """Performance testing utilities and benchmarks."""
    
    def __init__(self, temp_dir):
        self.temp_dir = Path(temp_dir)
        self.metrics = {}
    
    def measure_operation(self, operation_name, func, *args, **kwargs):
        """Measure execution time of an operation."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        metrics = {
            'duration': end_time - start_time,
            'memory_delta': end_memory - start_memory,
            'success': success,
            'error': error
        }
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(metrics)
        
        return result, metrics
    
    def _get_memory_usage(self):
        """Get current memory usage (simplified)."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0  # Fallback if psutil not available
    
    def get_performance_summary(self):
        """Get summary of performance metrics."""
        summary = {}
        
        for operation, measurements in self.metrics.items():
            successful = [m for m in measurements if m['success']]
            
            if successful:
                durations = [m['duration'] for m in successful]
                memory_deltas = [m['memory_delta'] for m in successful]
                
                summary[operation] = {
                    'count': len(measurements),
                    'success_rate': len(successful) / len(measurements),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'avg_memory_delta': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0
                }
        
        return summary


class TestPerformanceAndLoad:
    """Test system performance under various load conditions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.perf_suite = PerformanceTestSuite(self.temp_dir)
        self.config = {
            'macos': {
                'archivePath': str(Path(self.temp_dir) / 'archive'),
                'demoPath': str(Path(self.temp_dir) / 'demo'),
                'logbookPath': str(Path(self.temp_dir) / 'logbook')
            }
        }
        
        # Create directories
        for path in self.config['macos'].values():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_large_file_processing_performance(self):
        """Test performance with large files."""
        # Create files of various sizes
        file_sizes = [
            (1024, "1KB"),           # Small
            (1024 * 1024, "1MB"),    # Medium
            (10 * 1024 * 1024, "10MB"),  # Large
            (50 * 1024 * 1024, "50MB")   # Very large
        ]
        
        source_dir = Path(self.temp_dir) / "large_files"
        source_dir.mkdir()
        
        for size, size_name in file_sizes:
            # Create file
            file_path = source_dir / f"test_file_{size_name}.dat"
            
            def create_large_file():
                with open(file_path, 'wb') as f:
                    # Write in chunks to avoid memory issues
                    chunk_size = min(size, 1024 * 1024)  # 1MB chunks max
                    remaining = size
                    
                    while remaining > 0:
                        write_size = min(chunk_size, remaining)
                        f.write(b"X" * write_size)
                        remaining -= write_size
            
            # Measure file creation
            _, create_metrics = self.perf_suite.measure_operation(
                f"create_file_{size_name}", create_large_file
            )
            
            # Measure file reading
            def read_large_file():
                with open(file_path, 'rb') as f:
                    data = f.read()
                return len(data)
            
            _, read_metrics = self.perf_suite.measure_operation(
                f"read_file_{size_name}", read_large_file
            )
            
            # Measure file copying
            def copy_large_file():
                import shutil
                dest_path = source_dir / f"copy_{size_name}.dat"
                shutil.copy2(file_path, dest_path)
                return dest_path.stat().st_size
            
            _, copy_metrics = self.perf_suite.measure_operation(
                f"copy_file_{size_name}", copy_large_file
            )
            
            print(f"✓ {size_name} file performance:")
            print(f"  Create: {create_metrics['duration']:.2f}s")
            print(f"  Read: {read_metrics['duration']:.2f}s")
            print(f"  Copy: {copy_metrics['duration']:.2f}s")
        
        # Performance assertions
        summary = self.perf_suite.get_performance_summary()
        
        # All operations should complete successfully
        for operation, stats in summary.items():
            assert stats['success_rate'] == 1.0, f"{operation} had failures"
            assert stats['avg_duration'] < 30.0, f"{operation} too slow: {stats['avg_duration']:.2f}s"
        
        print("✓ Large file processing performance test completed")
    
    def test_concurrent_file_operations(self):
        """Test performance with concurrent file operations."""
        num_threads = 5
        files_per_thread = 20
        
        source_dir = Path(self.temp_dir) / "concurrent_test"
        source_dir.mkdir()
        
        def worker_thread(thread_id):
            """Worker function for concurrent operations."""
            thread_metrics = []
            
            for i in range(files_per_thread):
                file_path = source_dir / f"thread_{thread_id}_file_{i}.txt"
                
                # Create file
                start_time = time.time()
                file_path.write_text(f"Content from thread {thread_id}, file {i}")
                create_time = time.time() - start_time
                
                # Read file
                start_time = time.time()
                content = file_path.read_text()
                read_time = time.time() - start_time
                
                # Verify content
                expected = f"Content from thread {thread_id}, file {i}"
                assert content == expected
                
                thread_metrics.append({
                    'thread_id': thread_id,
                    'file_id': i,
                    'create_time': create_time,
                    'read_time': read_time
                })
            
            return thread_metrics
        
        # Run concurrent operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        all_metrics = []
        for thread_results in results:
            all_metrics.extend(thread_results)
        
        total_operations = len(all_metrics)
        avg_create_time = sum(m['create_time'] for m in all_metrics) / total_operations
        avg_read_time = sum(m['read_time'] for m in all_metrics) / total_operations
        
        print(f"✓ Concurrent operations performance:")
        print(f"  Threads: {num_threads}")
        print(f"  Files per thread: {files_per_thread}")
        print(f"  Total operations: {total_operations}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average create time: {avg_create_time * 1000:.2f}ms")
        print(f"  Average read time: {avg_read_time * 1000:.2f}ms")
        print(f"  Operations per second: {total_operations / total_time:.1f}")
        
        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert avg_create_time < 0.1  # Create operations should be fast
        assert avg_read_time < 0.1   # Read operations should be fast
        
        print("✓ Concurrent file operations test completed")
    
    def test_memory_usage_under_load(self):
        """Test memory usage patterns under load."""
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("⚠ psutil not available, skipping memory test")
            return
        
        initial_memory = process.memory_info().rss
        memory_samples = [initial_memory]
        
        # Create memory-intensive operations
        data_sets = []
        
        for i in range(10):
            # Create large data structure
            large_data = {
                'id': i,
                'data': 'X' * (1024 * 1024),  # 1MB string
                'metadata': {
                    'created': time.time(),
                    'size': 1024 * 1024,
                    'type': 'test_data'
                }
            }
            
            data_sets.append(large_data)
            
            # Sample memory usage
            current_memory = process.memory_info().rss
            memory_samples.append(current_memory)
            
            print(f"  Dataset {i+1}: Memory = {current_memory / 1024 / 1024:.1f}MB")
        
        peak_memory = max(memory_samples)
        memory_growth = peak_memory - initial_memory
        
        # Clean up data
        data_sets.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_recovered = peak_memory - final_memory
        
        print(f"✓ Memory usage analysis:")
        print(f"  Initial memory: {initial_memory / 1024 / 1024:.1f}MB")
        print(f"  Peak memory: {peak_memory / 1024 / 1024:.1f}MB")
        print(f"  Memory growth: {memory_growth / 1024 / 1024:.1f}MB")
        print(f"  Final memory: {final_memory / 1024 / 1024:.1f}MB")
        print(f"  Memory recovered: {memory_recovered / 1024 / 1024:.1f}MB")
        
        # Memory assertions
        assert memory_growth < 500 * 1024 * 1024  # Should not grow more than 500MB
        recovery_rate = memory_recovered / memory_growth if memory_growth > 0 else 1.0
        assert recovery_rate > 0.5  # Should recover at least 50% of memory
        
        print("✓ Memory usage under load test completed")
    
    def test_disk_io_performance(self):
        """Test disk I/O performance patterns."""
        test_dir = Path(self.temp_dir) / "disk_io_test"
        test_dir.mkdir()
        
        # Test sequential write performance
        def sequential_write_test():
            file_path = test_dir / "sequential_write.dat"
            chunk_size = 64 * 1024  # 64KB chunks
            num_chunks = 100
            
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                for i in range(num_chunks):
                    data = bytes(range(256)) * (chunk_size // 256)
                    f.write(data)
            
            duration = time.time() - start_time
            total_size = chunk_size * num_chunks
            throughput = total_size / duration
            
            return {
                'duration': duration,
                'size': total_size,
                'throughput': throughput
            }
        
        # Test random write performance
        def random_write_test():
            import random
            
            file_path = test_dir / "random_write.dat"
            chunk_size = 4 * 1024  # 4KB chunks
            num_chunks = 100
            
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                positions = list(range(num_chunks))
                random.shuffle(positions)
                
                for pos in positions:
                    f.seek(pos * chunk_size)
                    data = bytes(range(256)) * (chunk_size // 256)
                    f.write(data)
            
            duration = time.time() - start_time
            total_size = chunk_size * num_chunks
            throughput = total_size / duration
            
            return {
                'duration': duration,
                'size': total_size,
                'throughput': throughput
            }
        
        # Test read performance
        def read_test():
            file_path = test_dir / "sequential_write.dat"
            
            start_time = time.time()
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            duration = time.time() - start_time
            size = len(data)
            throughput = size / duration
            
            return {
                'duration': duration,
                'size': size,
                'throughput': throughput
            }
        
        # Run tests
        seq_write_result = sequential_write_test()
        rand_write_result = random_write_test()
        read_result = read_test()
        
        print(f"✓ Disk I/O performance:")
        print(f"  Sequential write: {seq_write_result['throughput'] / 1024 / 1024:.1f}MB/s")
        print(f"  Random write: {rand_write_result['throughput'] / 1024 / 1024:.1f}MB/s")
        print(f"  Read: {read_result['throughput'] / 1024 / 1024:.1f}MB/s")
        
        # Performance assertions
        min_throughput = 1024 * 1024  # 1MB/s minimum
        assert seq_write_result['throughput'] > min_throughput
        assert read_result['throughput'] > min_throughput
        
        print("✓ Disk I/O performance test completed")
    
    def test_scalability_with_file_count(self):
        """Test system scalability with increasing file counts."""
        file_counts = [100, 500, 1000, 2000]
        scalability_results = []
        
        for file_count in file_counts:
            test_dir = Path(self.temp_dir) / f"scale_test_{file_count}"
            test_dir.mkdir()
            
            # Create files
            start_time = time.time()
            
            for i in range(file_count):
                file_path = test_dir / f"file_{i:06d}.txt"
                file_path.write_text(f"Content for file {i}")
            
            create_time = time.time() - start_time
            
            # List files
            start_time = time.time()
            file_list = list(test_dir.glob("*.txt"))
            list_time = time.time() - start_time
            
            # Process files (read all)
            start_time = time.time()
            
            total_content_length = 0
            for file_path in file_list:
                content = file_path.read_text()
                total_content_length += len(content)
            
            process_time = time.time() - start_time
            
            result = {
                'file_count': file_count,
                'create_time': create_time,
                'list_time': list_time,
                'process_time': process_time,
                'total_time': create_time + list_time + process_time,
                'files_per_second': file_count / (create_time + process_time)
            }
            
            scalability_results.append(result)
            
            print(f"✓ {file_count} files:")
            print(f"  Create: {create_time:.2f}s")
            print(f"  List: {list_time:.2f}s")
            print(f"  Process: {process_time:.2f}s")
            print(f"  Files/sec: {result['files_per_second']:.1f}")
        
        # Analyze scalability
        print(f"\n✓ Scalability analysis:")
        for i in range(1, len(scalability_results)):
            prev_result = scalability_results[i-1]
            curr_result = scalability_results[i]
            
            file_ratio = curr_result['file_count'] / prev_result['file_count']
            time_ratio = curr_result['total_time'] / prev_result['total_time']
            
            efficiency = file_ratio / time_ratio
            
            print(f"  {prev_result['file_count']} -> {curr_result['file_count']} files: "
                  f"Efficiency = {efficiency:.2f}")
            
            # Efficiency should be reasonable (not too much worse than linear)
            assert efficiency > 0.5, f"Poor scalability: {efficiency:.2f}"
        
        print("✓ Scalability with file count test completed")
    
    def test_stress_test_continuous_operations(self):
        """Test system under continuous stress operations."""
        duration_seconds = 10  # Run for 10 seconds
        operations_count = 0
        errors_count = 0
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        stress_dir = Path(self.temp_dir) / "stress_test"
        stress_dir.mkdir()
        
        print(f"✓ Running stress test for {duration_seconds} seconds...")
        
        while time.time() < end_time:
            try:
                # Random operation
                import random
                operation = random.choice(['create', 'read', 'modify', 'delete'])
                
                if operation == 'create':
                    file_path = stress_dir / f"stress_{operations_count}.txt"
                    file_path.write_text(f"Stress test content {operations_count}")
                
                elif operation == 'read':
                    files = list(stress_dir.glob("*.txt"))
                    if files:
                        random_file = random.choice(files)
                        content = random_file.read_text()
                
                elif operation == 'modify':
                    files = list(stress_dir.glob("*.txt"))
                    if files:
                        random_file = random.choice(files)
                        current_content = random_file.read_text()
                        random_file.write_text(current_content + f" modified_{operations_count}")
                
                elif operation == 'delete':
                    files = list(stress_dir.glob("*.txt"))
                    if files and len(files) > 10:  # Keep some files
                        random_file = random.choice(files)
                        random_file.unlink()
                
                operations_count += 1
                
            except Exception as e:
                errors_count += 1
                if errors_count > operations_count * 0.1:  # More than 10% errors
                    print(f"  ⚠ High error rate: {errors_count}/{operations_count}")
                    break
        
        actual_duration = time.time() - start_time
        operations_per_second = operations_count / actual_duration
        error_rate = errors_count / operations_count if operations_count > 0 else 0
        
        # Final file count
        final_files = len(list(stress_dir.glob("*.txt")))
        
        print(f"✓ Stress test results:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Operations: {operations_count}")
        print(f"  Operations/sec: {operations_per_second:.1f}")
        print(f"  Errors: {errors_count}")
        print(f"  Error rate: {error_rate * 100:.1f}%")
        print(f"  Final files: {final_files}")
        
        # Stress test assertions
        assert operations_count > 0
        assert error_rate < 0.05  # Less than 5% error rate
        assert operations_per_second > 10  # At least 10 operations per second
        
        print("✓ Stress test continuous operations completed")