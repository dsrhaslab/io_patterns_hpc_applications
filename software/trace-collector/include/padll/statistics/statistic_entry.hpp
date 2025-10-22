/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#ifndef PADLL_STATISTIC_ENTRY_H
#define PADLL_STATISTIC_ENTRY_H

#include <cstdint>
#include <mutex>
#include <sstream>
#include <string>

namespace padll::stats {

/**
 * StatisticEntry class.
 * This class keeps track of all statistics that respect to a given operation.
 */
class StatisticEntry {

private:
    std::string m_entry_name {};
    std::string m_timestamp {};
    std::string m_process_id {};
    std::string m_thread_id {};
    std::string m_node {};
    std::string m_descriptor {};
    std::string m_file_path {};
    std::string m_file_new_path {};
    std::string m_offset {};
    std::string m_size {};
    std::string m_result {};

public:
    /**
     * StatisticEntry default constructor.
     */
    StatisticEntry ();

    /**
     * StatisticEntry parameterized constructor.
     * @param name
     */
    explicit StatisticEntry (const std::string& name);

        /**
     * StatisticEntry parameterized constructor.
     * @param name
     */
    StatisticEntry (
        std::string& name,
        std::string& timestamp,
        std::string& process_id,
        std::string& thread_id,
        std::string& node,
        std::string& descriptor,
        std::string& file_path,
        std::string& file_new_path,
        std::string& offset,
        std::string& size,
        std::string& result
    );

    /**
     * StatisticEntry copy constructor.
     * @param entry
     */
    StatisticEntry (const StatisticEntry& entry);

    /**
     * StatisticEntry default destructor.
     */
    ~StatisticEntry ();

    /**
     * get_entry_name: Get the name of the StatisticEntry object.
     * @return Returns a copy of the m_entry_name parameter.
     */
    [[nodiscard]] std::string get_entry_name () const;

    [[nodiscard]] std::string get_timestamp ();

    [[nodiscard]] std::string get_thread_id ();

    [[nodiscard]] std::string get_process_id ();

    [[nodiscard]] std::string get_node ();

    [[nodiscard]] std::string get_descriptor ();

    [[nodiscard]] std::string get_file_path ();

    [[nodiscard]] std::string get_file_new_path ();

    [[nodiscard]] std::string get_offset();

    [[nodiscard]] std::string get_size ();

    [[nodiscard]] std::string get_result ();

    /**
     * to_string: generate a string-based format of the contents of the StatisticEntry object.
     * @return String containing the current values of all StatisticEntry elements.
     */
    std::string to_string ();
    void set_timestamp (std::string timestamp);
    void set_thread_id (std::string thread_id);
    void set_process_id (std::string process_id);
    void set_offset (std::string offset);
};
} // namespace padll::stats

#endif // PADLL_STATISTIC_ENTRY_H
