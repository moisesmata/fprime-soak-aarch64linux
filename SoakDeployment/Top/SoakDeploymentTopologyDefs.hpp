// ======================================================================
// \title  SoakDeploymentTopologyDefs.hpp
// \brief required header file containing the required definitions for the topology autocoder
//
// ======================================================================
#ifndef SOAKDEPLOYMENT_SOAKDEPLOYMENTTOPOLOGYDEFS_HPP
#define SOAKDEPLOYMENT_SOAKDEPLOYMENTTOPOLOGYDEFS_HPP

// Subtopology PingEntries includes
#include "Svc/Subtopologies/CdhCore/PingEntries.hpp"
#include "Svc/Subtopologies/ComFprime/PingEntries.hpp"
#include "Svc/Subtopologies/DataProducts/PingEntries.hpp"
#include "Svc/Subtopologies/FileHandling/PingEntries.hpp"

#include "EventLoggerTee/PingEntries.hpp"
#include "TlmLoggerTee/PingEntries.hpp"

// SubtopologyTopologyDefs includes
#include "Svc/Subtopologies/ComFprime/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/DataProducts/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/FileHandling/SubtopologyTopologyDefs.hpp"

// Include autocoded FPP constants
#include "SoakDeployment/Top/FppConstantsAc.hpp"

/**
 * \brief required ping constants
 *
 * The topology autocoder requires a WARN and FATAL constant definition for each component that supports the health-ping
 * interface. These are expressed as enum constants placed in a namespace named for the component instance. These
 * are all placed in the PingEntries namespace.
 *
 * Each constant specifies how many missed pings are allowed before a WARNING_HI/FATAL event is triggered. In the
 * following example, the health component will emit a WARNING_HI event if the component instance cmdDisp does not
 * respond for 3 pings and will FATAL if responses are not received after a total of 5 pings.
 *
 * ```c++
 * namespace PingEntries {
 * namespace cmdDisp {
 *     enum { WARN = 3, FATAL = 5 };
 * }
 * }
 * ```
 */
namespace PingEntries {
    namespace SoakDeployment_rateGroup1 {enum { WARN = 3, FATAL = 5 };}
    namespace SoakDeployment_rateGroup2 {enum { WARN = 3, FATAL = 5 };}
    namespace SoakDeployment_rateGroup3 {enum { WARN = 3, FATAL = 5 };}
}  // namespace PingEntries

// Definitions are placed within a namespace named after the deployment
namespace SoakDeployment {

/**
 * \brief required type definition to carry state
 *
 * The topology autocoder requires an object that carries state with the name `SoakDeployment::TopologyState`. Only the type
 * definition is required by the autocoder and the contents of this object are otherwise opaque to the autocoder. The
 * contents are entirely up to the definition of the project. This deployment uses subtopologies, so the state contains
 * the subtopology state structures which are derived from command line inputs.
 */
struct TopologyState {
    ComFprime::SubtopologyState comFprime;  //!< Subtopology state for ComFprime
};

namespace PingEntries = ::PingEntries;
}  // namespace SoakDeployment
#endif
