/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#ifndef PADLL_OPTIONS_HPP
#define PADLL_OPTIONS_HPP

#include <filesystem>
#include <string>
#include <vector>

namespace padll::options {

/***************************************************************************************************
 * PADLL default configurations
 **************************************************************************************************/

/**
 * option_library_name: targeted dynamic library to LD_PRELOAD
 */
constexpr std::string_view option_library_name { "libc.so.6" };

/**
 * option_default_statistic_collection: option to enable/disable collection of LD_PRELOADED and
 * passthrough POSIX operations.
 */
constexpr bool option_default_statistic_collection { true };

/**
 * option_mount_point_differentiation_enabled: option to enable/disable mountpoint differentiation
 * and further selection of workflow identifiers (workflow-id to be submitted to the PAIO data
 * plane). All operations are considered with the same set of workflow identifiers
 */
constexpr bool option_mount_point_differentiation_enabled { true };

/**
 * option_check_local_mount_point_first:
 *  if option_mount_point_differentiation = true, first check if the path to be extracted is in the
 *  local mount point. If not, check if it is in the remote mount point.
 * FIXME: Needing refactor or cleanup -@gsd at 4/13/2022, 2:39:45 PM
 * Do not consider right now differentiation between local and remote mount points.
 */
// constexpr bool option_check_local_mount_point_first { true };

/**
 * option_default_local_mount_point:
 *  operations will pick from a selected set of workflow identifiers
 * FIXME: Needing refactor or cleanup -@gsd at 4/13/2022, 2:16:25 PM
 * Do not consider right now differentiation between local and remote mount points.
 */
// constexpr std::string_view option_default_local_mount_point { "/local" };
// constexpr std::string_view option_default_local_mount_point { "/tmp" };

/**
 * option_default_remote_mount_point: set the default main path of the remote mountpoint registry.
 * Operations will pick from a selected set of workflow identifiers.
 */
constexpr std::string_view option_default_remote_mount_point { "/tmp" };

/**
 * option_hard_remove: option to remove file descriptors from LdPreloadedPosix's m_mount_point_table
 * on ::close, even if the original fd was not registered due to process-based operations.
 */
constexpr bool option_hard_remove { false };

/**
 * option_default_metadata_server_unit: option to enable/disable the selection of a workflow-id for
 * a given MDS or MDT. This feature is still work-in-progress.
 */
constexpr bool option_select_workflow_by_metadata_unit { false };

/**
 * option_padll_workflows: get the number of internal workflows used by the PADLL data plane stage.
 * @return: returns the number of workflows to set in the data plane stage.
 *  May throw runtime_error exceptions if the padll_workflows are not set or are invalid values (<
 * 0).
 */
inline int option_padll_workflows ()
{
    // get value from environment variable
    auto workflows_env = std::getenv ("padll_workflows");

    // validate if variable was set
    if (workflows_env != nullptr) {
        auto workflows = std::stoi (workflows_env);

        // validate total of workflows
        if (workflows > 0) {
            return workflows;
        } else {
            throw std::runtime_error ("Invalid amount of workflows ('padll_workflows').");
        }
    } else {
        throw std::runtime_error ("Environment variable 'padll_workflows' not set.");
    }
}

/***************************************************************************************************
 * Log configuration
 **************************************************************************************************/

/**
 * option_default_enable_debug_level: option to enable/disable DEBUG level logging (i.e., log_debug
 * messages).
 */
constexpr bool option_default_enable_debug_level { false };

/**
 * option_default_enable_debug_with_ld_preload:
 */
constexpr bool option_default_enable_debug_with_ld_preload { false };

/**
 * option_default_log_path: default path (and file extension) for PADLL logging files.
 */
constexpr std::string_view option_default_log_path { "/tmp/padll-info" };

/**
 * option_default_detailed_logging: option to enable/disable detailed logging. Recommended only for
 * debugging/instrumentation.
 */
#define OPTION_DETAILED_LOGGING false

/**
 * option_default_with_logging: option to enable/disable logging. Disactivate if running programs with mpirun.
 */
#define OPTION_WITH_LOGGING false

/**
 * option_default_table_format: option to enable/disable visualization of statistics in tabular
 * format.
 */
constexpr bool option_default_table_format { false };

/**
 * option_default_save_statistics_report: option to enable/disable saving in a file the ldpreloaded
 * and passthrough statistics.
 */
constexpr bool option_default_save_statistics_report { true };

/**
 * option_default_statistics_report_path: main path to store the statistics files.
 */
constexpr std::string_view option_default_statistics_report_path { "/home1/10441/ritavaz02/tst/" };

constexpr long option_max_buffer_size{ 100000 };

} // namespace padll::options

#endif // PADLL_OPTIONS_HPP
