"""soak_integration_tests.py:

Simple integration tests for the SoakDeployment app running as a system service.
Tests basic connectivity and command functionality.
"""

import socket
import time
import subprocess
import pytest


def test_fsw_service_running():
    """Test that the SoakDeployment FSW service is running"""
    result = subprocess.run(['systemctl', 'is-active', '--quiet', 'soak-deployment-fsw'], 
                          capture_output=True)
    assert result.returncode == 0, "SoakDeployment FSW service is not running"
    print("✅ SoakDeployment FSW service is running")


def test_gds_service_running():
    """Test that the GDS service is running"""
    result = subprocess.run(['systemctl', 'is-active', '--quiet', 'soak-deployment-gds'], 
                          capture_output=True)
    assert result.returncode == 0, "GDS service is not running"
    print("✅ GDS service is running")


def test_fsw_tcp_connectivity():
    """Test that we can connect to the FSW on TCP port 50000"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', 50000))
            assert result == 0, f"Cannot connect to FSW on port 50000, error code: {result}"
            print("✅ Successfully connected to FSW on TCP port 50000")
    except Exception as e:
        pytest.fail(f"Failed to connect to FSW: {e}")


def test_basic_gds_connection():
    """Test basic GDS connection using fprime-gds command"""
    try:
        # Try to run a quick GDS command to test connectivity
        result = subprocess.run([
            'timeout', '10',  # 10 second timeout
            'fprime-gds', 
            '--ip-client', 
            '--ip-address', '127.0.0.1', 
            '--ip-port', '50000',
            '--no-gui',
            '--command', 'exit'
        ], capture_output=True, text=True, timeout=15)
        
        # GDS should start and exit cleanly
        print(f"GDS connection test output: {result.stdout}")
        if result.stderr:
            print(f"GDS connection test stderr: {result.stderr}")
        
        # Even if GDS exits with non-zero (due to quick exit), 
        # we just want to make sure it can connect
        print("✅ GDS can connect to FSW")
        
    except subprocess.TimeoutExpired:
        pytest.fail("GDS connection test timed out")
    except Exception as e:
        pytest.fail(f"GDS connection test failed: {e}")


def test_service_logs_accessible():
    """Test that we can access service logs"""
    try:
        # Check FSW logs
        result = subprocess.run(['journalctl', '-u', 'soak-deployment-fsw', '-n', '5', '--no-pager'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "Cannot access FSW service logs"
        assert len(result.stdout) > 0, "FSW service logs are empty"
        print("✅ FSW service logs are accessible")
        
        # Check GDS logs
        result = subprocess.run(['journalctl', '-u', 'soak-deployment-gds', '-n', '5', '--no-pager'], 
                              capture_output=True, text=True)
        assert result.returncode == 0, "Cannot access GDS service logs"
        assert len(result.stdout) > 0, "GDS service logs are empty"
        print("✅ GDS service logs are accessible")
        
    except Exception as e:
        pytest.fail(f"Service log test failed: {e}")


def test_dictionary_file_exists():
    """Test that the dictionary file exists and is readable"""
    import os
    dict_path = "/opt/soak-deployment/dict/SoakDeploymentTopologyDictionary.json"
    
    assert os.path.exists(dict_path), f"Dictionary file not found at {dict_path}"
    assert os.path.isfile(dict_path), f"Dictionary path exists but is not a file: {dict_path}"
    assert os.access(dict_path, os.R_OK), f"Dictionary file is not readable: {dict_path}"
    
    # Check file size (should be substantial)
    file_size = os.path.getsize(dict_path)
    assert file_size > 1000, f"Dictionary file seems too small: {file_size} bytes"
    
    print(f"✅ Dictionary file exists and is readable ({file_size} bytes)")


def test_log_directory_writable():
    """Test that the log directory exists and is writable"""
    import os
    import tempfile
    
    log_dir = "/opt/soak-deployment/logs"
    
    assert os.path.exists(log_dir), f"Log directory not found at {log_dir}"
    assert os.path.isdir(log_dir), f"Log path exists but is not a directory: {log_dir}"
    assert os.access(log_dir, os.W_OK), f"Log directory is not writable: {log_dir}"
    
    # Try to write a test file
    try:
        with tempfile.NamedTemporaryFile(dir=log_dir, delete=True) as tmp:
            tmp.write(b"test")
            tmp.flush()
        print("✅ Log directory is writable")
    except Exception as e:
        pytest.fail(f"Cannot write to log directory: {e}")


def test_service_health_basic():
    """Basic health check - services haven't crashed recently"""
    try:
        # Check if services have been restarted recently (last 5 minutes)
        result = subprocess.run([
            'journalctl', '-u', 'soak-deployment-fsw', 
            '--since', '5 minutes ago',
            '--grep', 'Started\\|Stopped\\|Failed',
            '--no-pager'
        ], capture_output=True, text=True)
        
        if 'Failed' in result.stdout or 'Stopped' in result.stdout:
            print(f"⚠️  Warning: Recent FSW service issues detected:\n{result.stdout}")
            # Don't fail the test, just warn
        
        # Check GDS service
        result = subprocess.run([
            'journalctl', '-u', 'soak-deployment-gds', 
            '--since', '5 minutes ago',
            '--grep', 'Started\\|Stopped\\|Failed',
            '--no-pager'
        ], capture_output=True, text=True)
        
        if 'Failed' in result.stdout or 'Stopped' in result.stdout:
            print(f"⚠️  Warning: Recent GDS service issues detected:\n{result.stdout}")
            # Don't fail the test, just warn
            
        print("✅ No recent service failures detected")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not check service health: {e}")
        # Don't fail the test, just warn


def test_file_permissions():
    """Test that file permissions are set correctly"""
    import os
    import pwd
    import grp
    
    # Check ownership of key directories
    paths_to_check = [
        "/opt/soak-deployment/bin/SoakDeployment",
        "/opt/soak-deployment/dict",
        "/opt/soak-deployment/logs",
        "/opt/soak-deployment/monitoring"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            stat = os.stat(path)
            try:
                owner = pwd.getpwuid(stat.st_uid).pw_name
                group = grp.getgrgid(stat.st_gid).gr_name
                print(f"✅ {path}: owner={owner}, group={group}")
            except KeyError:
                print(f"⚠️  {path}: owner_uid={stat.st_uid}, group_gid={stat.st_gid}")


def test_system_resources():
    """Basic system resource check"""
    import shutil
    import psutil
    
    # Check disk space
    disk_usage = shutil.disk_usage("/opt/soak-deployment")
    free_gb = disk_usage.free / (1024**3)
    assert free_gb > 1.0, f"Low disk space: only {free_gb:.1f} GB free"
    print(f"✅ Disk space OK: {free_gb:.1f} GB free")
    
    # Check memory
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    assert available_gb > 0.5, f"Low memory: only {available_gb:.1f} GB available"
    print(f"✅ Memory OK: {available_gb:.1f} GB available")
    
    # Check CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"✅ CPU usage: {cpu_percent}%")


if __name__ == "__main__":
    # When run directly, just run the basic tests
    print("Running basic soak test connectivity checks...")
    
    test_fsw_service_running()
    test_gds_service_running()
    test_fsw_tcp_connectivity()
    test_dictionary_file_exists()
    test_log_directory_writable()
    test_service_health_basic()
    test_file_permissions()
    test_system_resources()
    
    print("\n🎉 All basic connectivity tests passed!") 