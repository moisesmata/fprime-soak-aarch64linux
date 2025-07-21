# SoakDeployment Integration Tests

This directory contains simplified integration tests for the SoakDeployment application running as a system service for soak testing.

## Files

- `soak_integration_tests.py`: Simple integration tests that verify:
  - **Service Status**: FSW and GDS services are running
  - **Network Connectivity**: TCP connection to FSW on port 50000
  - **GDS Connectivity**: Basic GDS connection test
  - **File System**: Dictionary files exist and log directories are writable
  - **Service Health**: No recent crashes or failures
  - **System Resources**: Basic disk space and memory checks
  - **File Permissions**: Correct ownership of key files

- `soak_test_seq.seq`: Test sequence file for validating command sequencing capabilities

- `logs/`: Directory for test logs and outputs (ignored by git)

## Usage

These tests are automatically run by the GitHub Actions workflow `ext-aarch64-linux-soak-test.yml` every 30 minutes when the schedule is enabled.

The tests can also be run manually using:

```bash
pytest --dictionary <path-to-dictionary> soak_integration_tests.py
```

Or run directly as a Python script for quick connectivity checks:

```bash
python3 soak_integration_tests.py
```

## Test Philosophy

These integration tests are designed specifically for **soak testing** with running system services:

1. **Service-Oriented**: Tests work with FSW and GDS running as systemd services
2. **Connectivity-Focused**: Verifies network connections and basic communication
3. **Non-Intrusive**: Tests don't interfere with ongoing soak operations
4. **Health Monitoring**: Checks for service stability and resource usage
5. **Rapid Execution**: Tests run quickly (< 30 seconds) for frequent monitoring

The tests are intentionally **simple and robust** rather than comprehensive. They focus on verifying that the soak test deployment is operational and healthy, not on testing complex F´ functionality.

## Requirements

The tests require:
- `systemctl` (for service status checks)
- `journalctl` (for log access)
- `psutil` Python package (for system resource monitoring)
- Network access to localhost:50000 (FSW TCP port)

## Expected Service Configuration

The tests assume the following systemd services are configured:
- `soak-deployment-fsw`: The F´ SoakDeployment binary running on port 50000
- `soak-deployment-gds`: The F´ GDS connecting to the FSW service

Files should be located at:
- `/opt/soak-deployment/bin/SoakDeployment` (FSW binary)
- `/opt/soak-deployment/dict/SoakDeploymentTopologyDictionary.json` (Dictionary)
- `/opt/soak-deployment/logs/` (Log directory) 