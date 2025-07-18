# SoakDeployment Integration Tests

This directory contains integration tests for the SoakDeployment application used for soak testing.

## Files

- `soak_integration_tests.py`: Main integration test file containing comprehensive tests for:
  - Basic telemetry streaming
  - Command dispatch and execution
  - Rate group health and timing
  - System resource monitoring
  - Communication queue health
  - Data products functionality
  - Event logging
  - Health monitoring
  - Command sequencer
  - File handling system
  - Continuous operation capabilities
  - Sequence generation and execution

- `soak_test_seq.seq`: Test sequence file for validating command sequencing capabilities

- `logs/`: Directory for test logs and outputs (ignored by git)

## Usage

These tests are automatically run by the GitHub Actions workflow `ext-aarch64-linux-soak-test.yml` every 30 minutes when the schedule is enabled.

The tests can also be run manually using:

```bash
pytest --dictionary <path-to-dictionary> soak_integration_tests.py
```

## Test Philosophy

These integration tests are designed specifically for soak testing, which means they:

1. **Verify continuous operation**: Tests ensure the system can run continuously without degradation
2. **Monitor critical health metrics**: Rate group timing, cycle slips, memory usage, etc.
3. **Test all major subsystems**: CDH, communication, data products, file handling, and logging
4. **Validate resource management**: Buffer management, queue depths, and system resources
5. **Ensure robustness**: The system should remain healthy during extended operation

The tests are more conservative than typical unit tests, focusing on system stability and long-term reliability rather than edge cases or stress testing. 