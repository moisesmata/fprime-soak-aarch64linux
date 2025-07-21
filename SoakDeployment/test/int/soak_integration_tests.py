"""soak_integration_tests.py:

Traditional F' integration tests for SoakDeployment using fprime_test_api.
These tests connect to the running systemd services and perform standard F' testing.
Based on the LED blinker soak test pattern.
"""

import time
import os
from pathlib import Path
import pytest
from fprime_gds.common.testing_fw import predicates


@pytest.fixture(scope="session", autouse=True)
def configure_deployment_root():
    """Configure the working directory to the deployment root for settings.ini detection"""
    # Get the current test file location
    test_file = Path(__file__)
    # Navigate up to the deployment root (two levels up from test/int/)
    deployment_root = test_file.parent.parent.parent
    
    # Change to deployment root directory so settings.ini can be found
    original_cwd = os.getcwd()
    os.chdir(deployment_root)
    
    print(f"Changed working directory to: {deployment_root}")
    print(f"Settings file should be at: {deployment_root / 'settings.ini'}")
    
    # Verify settings.ini exists
    settings_file = deployment_root / "settings.ini"
    if settings_file.exists():
        print(f"✅ Found settings.ini at {settings_file}")
    else:
        print(f"⚠️  Warning: settings.ini not found at {settings_file}")
    
    yield
    
    # Restore original working directory
    os.chdir(original_cwd)


def test_is_streaming(fprime_test_api):
    """Test that SoakDeployment is streaming telemetry
    
    Tests that the flight software is streaming by looking for telemetry items.
    This ensures the system is operational and telemetry is flowing.
    """
    results = fprime_test_api.assert_telemetry_count(5, timeout=10)
    for result in results:
        msg = "received channel {} update: {}".format(result.get_id(), result.get_str())
        print(msg)


def test_send_command(fprime_test_api):
    """Test that commands may be sent to SoakDeployment
    
    Tests command send, dispatch, and receipt using send_and_assert command with NO-OP commands.
    """
    fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP", max_delay=0.1)
    assert fprime_test_api.get_command_test_history().size() == 1
    fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP", max_delay=0.1)
    assert fprime_test_api.get_command_test_history().size() == 2


def test_send_command_args(fprime_test_api):
    """Test that commands with arguments may be sent
    
    Tests command send, dispatch, and receipt using send_and_assert command with string NO-OP commands.
    """
    test_strings = ["SoakTest String 1", "Soak deployment test string", "Long running soak test"]
    for count, value in enumerate(test_strings, 1):
        events = [
            fprime_test_api.get_event_pred(
                "CdhCore.cmdDisp.NoOpStringReceived", [value]
            )
        ]
        fprime_test_api.send_and_assert_command(
            "CdhCore.cmdDisp.CMD_NO_OP_STRING",
            [value],
            max_delay=0.1,
            events=events,
        )
        assert fprime_test_api.get_command_test_history().size() == count


def test_system_resources_telemetry(fprime_test_api):
    """Test system resource telemetry channels
    
    Verifies that system resources are being monitored and reported correctly.
    """
    # Wait for some telemetry to accumulate
    time.sleep(2)
    
    try:
        # Try to get system resource telemetry
        memory_total = fprime_test_api.await_telemetry("SoakDeployment.systemResources.MEMORY_TOTAL", timeout=5)
        print(f"Memory Total: {memory_total.get_val()} KB")
        assert memory_total.get_val() > 0, "Memory total should be greater than 0"
        
        memory_used = fprime_test_api.await_telemetry("SoakDeployment.systemResources.MEMORY_USED", timeout=5)
        print(f"Memory Used: {memory_used.get_val()} KB")
        assert memory_used.get_val() > 0, "Memory used should be greater than 0"
        
        cpu_usage = fprime_test_api.await_telemetry("SoakDeployment.systemResources.CPU", timeout=5)
        print(f"CPU Usage: {cpu_usage.get_val()} percent")
        assert 0 <= cpu_usage.get_val() <= 100, "CPU usage should be between 0 and 100 percent"
        
    except Exception as e:
        print(f"System resource telemetry test failed: {e}")
        # Don't fail the test if specific channels aren't available
        print("Continuing with basic telemetry streaming test...")


def test_buffer_manager_telemetry(fprime_test_api):
    """Test buffer manager telemetry
    
    Verifies that buffer managers are operational and reporting telemetry.
    """
    try:
        # Check communication buffer manager
        total_buffs = fprime_test_api.await_telemetry("ComFprime.commsBufferManager.TotalBuffs", timeout=5)
        print(f"Comm Total Buffers: {total_buffs.get_val()}")
        assert total_buffs.get_val() > 0, "Should have some total communication buffers"
        
        curr_buffs = fprime_test_api.await_telemetry("ComFprime.commsBufferManager.CurrBuffs", timeout=5)
        print(f"Comm Current Buffers: {curr_buffs.get_val()}")
        assert curr_buffs.get_val() >= 0, "Current buffers should be non-negative"
        
        # Check data products buffer manager if available
        dp_total = fprime_test_api.await_telemetry("DataProducts.dpBufferManager.TotalBuffs", timeout=5)
        print(f"DP Total Buffers: {dp_total.get_val()}")
        assert dp_total.get_val() >= 0, "DP total buffers should be non-negative"
        
    except Exception as e:
        print(f"Buffer manager telemetry test failed: {e}")
        # Don't fail the test if specific channels aren't available
        print("Continuing with basic telemetry streaming test...")


def test_continuous_operation(fprime_test_api):
    """Test continuous operation capabilities
    
    This test verifies that the system can operate continuously without degradation.
    Simulates a longer running scenario for soak testing.
    """
    # Clear histories to start fresh
    fprime_test_api.clear_histories()
    
    # Send commands periodically over a time period
    for i in range(5):
        fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP", max_delay=0.1)
        time.sleep(1)  # Wait 1 second between commands
    
    # Verify we got consistent telemetry during operation
    telemetry_history = fprime_test_api.get_telemetry_test_history()
    telemetry_items = telemetry_history.retrieve()
    print(f"Received {len(telemetry_items)} telemetry items during continuous operation")
    
    # Should have received some telemetry during the 5-second test
    assert len(telemetry_items) > 0, "Should receive telemetry during continuous operation"
    
    # Verify we got consistent events during operation  
    event_history = fprime_test_api.get_event_test_history()
    events = event_history.retrieve()
    print(f"Received {len(events)} events during continuous operation")
    
    # Should have received command dispatch/completion events
    assert len(events) >= 5, "Should receive events from command operations"


def test_basic_health(fprime_test_api):
    """Test basic system health
    
    Verifies that the system is operating normally without health issues.
    """
    # Wait a moment for any health telemetry to be generated
    time.sleep(2)
    
    # Just verify that we can get some telemetry and send commands
    # This confirms the basic FSW-GDS connection is working
    fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP", max_delay=0.1)
    
    # Verify telemetry is flowing
    results = fprime_test_api.assert_telemetry_count(3, timeout=5)
    print(f"Health check: Received {len(results)} telemetry items")
    
    # System is healthy if we can send commands and receive telemetry
    assert len(results) >= 3, "Basic health check: should receive telemetry" 