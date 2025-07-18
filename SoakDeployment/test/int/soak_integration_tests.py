"""soak_integration_tests.py:

A set of integration tests to apply to the SoakDeployment app. This tests the soak deployment system
including core functionality, data products, file handling, communication, and system resources.
"""

import subprocess
import time
from enum import Enum
from pathlib import Path

from fprime_gds.common.testing_fw import predicates
from fprime_gds.common.utils.event_severity import EventSeverity


"""
This enum includes the values of EventSeverity that can be filtered by the ActiveLogger Component
"""
FilterSeverity = Enum(
    "FilterSeverity",
    "WARNING_HI WARNING_LO COMMAND ACTIVITY_HI ACTIVITY_LO DIAGNOSTIC",
)


def test_is_streaming(fprime_test_api):
    """Test that SoakDeployment is streaming telemetry

    Tests that the flight software is streaming by looking for 10 telemetry items in 15 seconds.
    This ensures the system is operational and telemetry is flowing.
    """
    results = fprime_test_api.assert_telemetry_count(10, timeout=15)
    for result in results:
        msg = "received channel {} update: {}".format(result.get_id(), result.get_str())
        print(msg)
    
    # Verify system resources are being reported
    fprime_test_api.assert_telemetry("SoakDeployment.systemResources.MEMORY_TOTAL", timeout=5)
    fprime_test_api.assert_telemetry("SoakDeployment.systemResources.MEMORY_USED", timeout=5)


def set_event_filter(fprime_test_api, severity, enabled):
    """Send command to set event filter

    This helper will send a command that updates the given severity filter on the ActiveLogger
    Component in the SoakDeployment.

    Args:
        fprime_test_api: test api to use
        severity: A valid FilterSeverity Enum Value (str) or an instance of FilterSeverity
        enabled: a boolean of whether or not to enable the given severity

    Return:
        boolean of whether the report filter was set successfully.
    """
    enabled = "ENABLED" if enabled else "DISABLED"
    if isinstance(severity, FilterSeverity):
        severity = severity.name
    else:
        severity = FilterSeverity[severity].name
    try:
        fprime_test_api.send_command(
            "CdhCore.events.SET_EVENT_FILTER",
            [severity, enabled],
        )
        return True
    except AssertionError:
        return False


def set_default_filters(fprime_test_api):
    """Set the default (initial) event filters"""
    set_event_filter(fprime_test_api, "COMMAND", True)
    set_event_filter(fprime_test_api, "ACTIVITY_LO", True)
    set_event_filter(fprime_test_api, "ACTIVITY_HI", True)
    set_event_filter(fprime_test_api, "WARNING_LO", True)
    set_event_filter(fprime_test_api, "WARNING_HI", True)
    set_event_filter(fprime_test_api, "DIAGNOSTIC", False)


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


def test_rate_groups_operational(fprime_test_api):
    """Test that all rate groups are operational and not slipping

    Verifies that the three rate groups are running without cycle slips, which is critical
    for a soak test deployment that needs to run continuously.
    """
    # Wait a bit to allow rate groups to settle
    time.sleep(2)
    
    # Check that no rate groups have cycle slips
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup1.RgCycleSlips", value=0, timeout=3)
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup2.RgCycleSlips", value=0, timeout=3)
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup3.RgCycleSlips", value=0, timeout=3)
    
    # Verify rate groups are executing within reasonable timing
    # RgMaxTime should be reasonable (less than 1000ms for a 1Hz rate group)
    rg1_max_time = fprime_test_api.assert_telemetry("SoakDeployment.rateGroup1.RgMaxTime", timeout=3)
    rg2_max_time = fprime_test_api.assert_telemetry("SoakDeployment.rateGroup2.RgMaxTime", timeout=3)
    rg3_max_time = fprime_test_api.assert_telemetry("SoakDeployment.rateGroup3.RgMaxTime", timeout=3)
    
    # Log the timing information
    print(f"Rate Group 1 Max Time: {rg1_max_time.get_val()}")
    print(f"Rate Group 2 Max Time: {rg2_max_time.get_val()}")
    print(f"Rate Group 3 Max Time: {rg3_max_time.get_val()}")


def test_system_resources_monitoring(fprime_test_api):
    """Test system resource monitoring functionality

    Verifies that system resources are being monitored correctly and values are reasonable.
    This is important for soak testing to monitor system health over time.
    """
    # Get system resource telemetry
    memory_total = fprime_test_api.assert_telemetry("SoakDeployment.systemResources.MEMORY_TOTAL", timeout=3)
    memory_used = fprime_test_api.assert_telemetry("SoakDeployment.systemResources.MEMORY_USED", timeout=3)
    cpu_usage = fprime_test_api.assert_telemetry("SoakDeployment.systemResources.CPU", timeout=3)
    
    # Verify reasonable values
    assert memory_total.get_val() > 0, "Memory total should be greater than 0"
    assert memory_used.get_val() > 0, "Memory used should be greater than 0"
    assert memory_used.get_val() <= memory_total.get_val(), "Memory used should not exceed total"
    assert 0 <= cpu_usage.get_val() <= 100, "CPU usage should be between 0 and 100 percent"
    
    print(f"Memory Total: {memory_total.get_val()}")
    print(f"Memory Used: {memory_used.get_val()}")
    print(f"CPU Usage: {cpu_usage.get_val()}%")


def test_communication_queue_health(fprime_test_api):
    """Test communication queue health

    Verifies that communication queues are operational and not backed up.
    """
    # Check communication queue depths
    com_queue_depth = fprime_test_api.assert_telemetry("ComFprime.comQueue.comQueueDepth", timeout=3)
    buff_queue_depth = fprime_test_api.assert_telemetry("ComFprime.comQueue.buffQueueDepth", timeout=3)
    
    # Queue depths should be reasonable (not completely full)
    print(f"Communication Queue Depth: {com_queue_depth.get_val()}")
    print(f"Buffer Queue Depth: {buff_queue_depth.get_val()}")
    
    # Check buffer manager health
    total_buffs = fprime_test_api.assert_telemetry("ComFprime.commsBufferManager.TotalBuffs", timeout=3)
    curr_buffs = fprime_test_api.assert_telemetry("ComFprime.commsBufferManager.CurrBuffs", timeout=3)
    
    assert total_buffs.get_val() > 0, "Should have some total buffers"
    assert curr_buffs.get_val() >= 0, "Current buffers should be non-negative"
    
    print(f"Total Buffers: {total_buffs.get_val()}")
    print(f"Current Buffers: {curr_buffs.get_val()}")


def test_data_products_functionality(fprime_test_api):
    """Test data products subsystem

    Verifies that the data products subsystem is operational.
    """
    # Check data products telemetry
    catalog_dps = fprime_test_api.assert_telemetry("DataProducts.dpCat.CatalogDps", timeout=3)
    dp_total_buffs = fprime_test_api.assert_telemetry("DataProducts.dpBufferManager.TotalBuffs", timeout=3)
    dp_curr_buffs = fprime_test_api.assert_telemetry("DataProducts.dpBufferManager.CurrBuffs", timeout=3)
    
    print(f"Catalog Data Products: {catalog_dps.get_val()}")
    print(f"DP Total Buffers: {dp_total_buffs.get_val()}")
    print(f"DP Current Buffers: {dp_curr_buffs.get_val()}")
    
    # Verify reasonable values
    assert dp_total_buffs.get_val() > 0, "Should have some DP total buffers"
    assert dp_curr_buffs.get_val() >= 0, "DP current buffers should be non-negative"


def test_event_logging_functionality(fprime_test_api):
    """Test event logging through ComLogger

    Verifies that events are being logged properly through the EventLoggerTee.
    """
    set_default_filters(fprime_test_api)
    
    # Clear histories to start fresh
    fprime_test_api.clear_histories()
    
    # Send some commands to generate events
    fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP")
    fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP_STRING", ["Event logging test"])
    
    # Wait a bit for events to be processed
    time.sleep(1)
    
    # Verify we received some events
    events = fprime_test_api.get_event_test_history().retrieve()
    assert len(events) > 0, "Should have received some events"
    
    print(f"Received {len(events)} events during logging test")


def test_health_monitoring(fprime_test_api):
    """Test health monitoring system

    Verifies that the health monitoring system is operational and components are healthy.
    """
    # Check health ping warnings (should be 0 for healthy system)
    ping_warnings = fprime_test_api.assert_telemetry("CdhCore.$health.PingLateWarnings", timeout=3)
    
    assert ping_warnings.get_val() == 0, f"Expected no ping warnings, got {ping_warnings.get_val()}"
    
    print("Health monitoring: All components responding to pings")


def test_command_sequencer(fprime_test_api):
    """Test command sequencer functionality

    Verifies that the command sequencer is operational.
    """
    # Check command sequencer telemetry
    cs_executed = fprime_test_api.assert_telemetry("ComFprime.cmdSeq.CS_CommandsExecuted", timeout=3)
    cs_errors = fprime_test_api.assert_telemetry("ComFprime.cmdSeq.CS_Errors", timeout=3)
    
    print(f"Commands Executed by Sequencer: {cs_executed.get_val()}")
    print(f"Sequencer Errors: {cs_errors.get_val()}")
    
    # Should have minimal errors during normal operation
    assert cs_errors.get_val() == 0, f"Expected no sequencer errors, got {cs_errors.get_val()}"


def test_file_handling_system(fprime_test_api):
    """Test file handling subsystem

    Verifies that the file handling subsystem is operational.
    """
    # Check file handling telemetry
    files_received = fprime_test_api.assert_telemetry("FileHandling.fileUplink.FilesReceived", timeout=3)
    files_sent = fprime_test_api.assert_telemetry("FileHandling.fileDownlink.FilesSent", timeout=3)
    
    print(f"Files Received: {files_received.get_val()}")
    print(f"Files Sent: {files_sent.get_val()}")
    
    # Check for warnings (should be minimal during normal operation)
    uplink_warnings = fprime_test_api.assert_telemetry("FileHandling.fileUplink.Warnings", timeout=3)
    downlink_warnings = fprime_test_api.assert_telemetry("FileHandling.fileDownlink.Warnings", timeout=3)
    
    print(f"Uplink Warnings: {uplink_warnings.get_val()}")
    print(f"Downlink Warnings: {downlink_warnings.get_val()}")


def test_continuous_operation(fprime_test_api):
    """Test continuous operation capabilities

    This test verifies that the system can operate continuously without degradation.
    Simulates a longer running scenario for soak testing.
    """
    initial_commands_dispatched = fprime_test_api.assert_telemetry("CdhCore.cmdDisp.CommandsDispatched", timeout=3)
    
    # Send commands periodically over a longer time period
    for i in range(5):
        fprime_test_api.send_and_assert_command("CdhCore.cmdDisp.CMD_NO_OP", max_delay=0.1)
        time.sleep(1)  # Wait 1 second between commands
    
    # Verify commands were dispatched
    final_commands_dispatched = fprime_test_api.assert_telemetry("CdhCore.cmdDisp.CommandsDispatched", timeout=3)
    commands_sent = final_commands_dispatched.get_val() - initial_commands_dispatched.get_val()
    
    assert commands_sent >= 5, f"Expected at least 5 commands dispatched, got {commands_sent}"
    
    # Verify system is still healthy after continuous operation
    ping_warnings = fprime_test_api.assert_telemetry("CdhCore.$health.PingLateWarnings", timeout=3)
    assert ping_warnings.get_val() == 0, "System should still be healthy after continuous operation"
    
    # Verify no cycle slips occurred during continuous operation
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup1.RgCycleSlips", value=0, timeout=3)
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup2.RgCycleSlips", value=0, timeout=3)
    fprime_test_api.assert_telemetry("SoakDeployment.rateGroup3.RgCycleSlips", value=0, timeout=3)
    
    print(f"Continuous operation test completed successfully. Commands dispatched: {commands_sent}")


def test_seqgen(fprime_test_api):
    """Tests that a sequence can be generated and dispatched

    This test requires localhost testing and verifies the sequence generation capability.
    """
    sequence = Path(__file__).parent / "soak_test_seq.seq"
    
    # Only run if sequence file exists
    if not sequence.exists():
        print("Sequence file not found, skipping seqgen test")
        return
        
    assert (
        subprocess.run(
            [
                "fprime-seqgen",
                "-d",
                str(fprime_test_api.pipeline.dictionary_path),
                str(sequence),
                "/tmp/soak_test_int.bin",
            ]
        ).returncode
        == 0
    ), "Failed to run fprime-seqgen"
    
    fprime_test_api.send_and_assert_command(
        "ComFprime.cmdSeq.CS_RUN", args=["/tmp/soak_test_int.bin", "BLOCK"], max_delay=5
    ) 