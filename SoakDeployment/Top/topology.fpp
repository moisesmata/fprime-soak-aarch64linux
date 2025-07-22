module SoakDeployment {

  # ----------------------------------------------------------------------
  # Symbolic constants for port numbers
  # ----------------------------------------------------------------------

  enum Ports_RateGroups {
    rateGroup1
    rateGroup2
    rateGroup3
  }

  topology SoakDeployment {

  # ----------------------------------------------------------------------
  # Subtopology imports
  # ----------------------------------------------------------------------
    import CdhCore.Subtopology
    import ComFprime.Subtopology
    import DataProducts.Subtopology
    import FileHandling.Subtopology

    import EventLoggerTee.Subtopology
    import TlmLoggerTee.Subtopology
    
  # ----------------------------------------------------------------------
  # Instances used in the topology
  # ----------------------------------------------------------------------

    instance chronoTime
    instance rateGroup1
    instance rateGroup2
    instance rateGroup3
    instance rateGroupDriver
    instance systemResources
    instance linuxTimer

  # ----------------------------------------------------------------------
  # Pattern graph specifiers
  # ----------------------------------------------------------------------

    command connections instance CdhCore.cmdDisp
    event connections instance CdhCore.events
    telemetry connections instance CdhCore.tlmSend
    text event connections instance CdhCore.textLogger
    health connections instance CdhCore.$health
    param connections instance FileHandling.prmDb
    time connections instance chronoTime

  # ----------------------------------------------------------------------
  # Telemetry packets
  # ----------------------------------------------------------------------

    include "SoakDeploymentPackets.fppi"

  # ----------------------------------------------------------------------
  # Direct graph specifiers
  # ----------------------------------------------------------------------

    connections ComFprime_CdhCore {
      # Core events and telemetry to communication queue
      CdhCore.events.PktSend -> ComFprime.comQueue.comPacketQueueIn[ComFprime.Ports_ComPacketQueue.EVENTS]
      CdhCore.tlmSend.PktSend -> ComFprime.comQueue.comPacketQueueIn[ComFprime.Ports_ComPacketQueue.TELEMETRY]

      # Router to Command Dispatcher
      ComFprime.fprimeRouter.commandOut -> CdhCore.cmdDisp.seqCmdBuff
      CdhCore.cmdDisp.seqCmdStatus -> ComFprime.fprimeRouter.cmdResponseIn
      
      # Command Sequencer
      ComFprime.cmdSeq.comCmdOut -> CdhCore.cmdDisp.seqCmdBuff
      CdhCore.cmdDisp.seqCmdStatus -> ComFprime.cmdSeq.cmdResponseIn
    }

    connections ComFprime_FileHandling {
      # File Downlink to Communication Queue
      FileHandling.fileDownlink.bufferSendOut -> ComFprime.comQueue.bufferQueueIn[FileHandling.Ports_ComBufferQueue.FILE_DOWNLINK]
      ComFprime.comQueue.bufferReturnOut[FileHandling.Ports_ComBufferQueue.FILE_DOWNLINK] -> FileHandling.fileDownlink.bufferReturn

      # Router to File Uplink
      ComFprime.fprimeRouter.fileOut -> FileHandling.fileUplink.bufferSendIn
      FileHandling.fileUplink.bufferSendOut -> ComFprime.fprimeRouter.fileBufferReturnIn
    }

    connections FileHandling_DataProducts {
      # Data Products to File Downlink
      DataProducts.dpCat.fileOut -> FileHandling.fileDownlink.SendFile
      FileHandling.fileDownlink.FileComplete -> DataProducts.dpCat.fileDone
    }

    connections RateGroups {
      # LinuxTimer to drive rate group
      linuxTimer.CycleOut -> rateGroupDriver.CycleIn

      # Rate group 1
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup1] -> rateGroup1.CycleIn
      rateGroup1.RateGroupMemberOut[0] -> CdhCore.tlmSend.Run
      rateGroup1.RateGroupMemberOut[1] -> FileHandling.fileDownlink.Run
      rateGroup1.RateGroupMemberOut[2] -> systemResources.run
      rateGroup1.RateGroupMemberOut[3] -> ComFprime.comQueue.run

      # Rate group 2
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
      rateGroup2.RateGroupMemberOut[0] -> ComFprime.cmdSeq.schedIn

      # Rate group 3
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup3] -> rateGroup3.CycleIn
      rateGroup3.RateGroupMemberOut[0] -> CdhCore.$health.Run
      rateGroup3.RateGroupMemberOut[1] -> ComFprime.commsBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[2] -> DataProducts.dpBufferManager.schedIn
      rateGroup3.RateGroupMemberOut[3] -> DataProducts.dpWriter.schedIn
      rateGroup3.RateGroupMemberOut[4] -> DataProducts.dpMgr.schedIn

    }

    connections SoakDeployment {
      # Add connections here to user-defined components
    }

  }

}
