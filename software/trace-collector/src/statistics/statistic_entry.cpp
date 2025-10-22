/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#include <cinttypes>
#include <padll/statistics/statistic_entry.hpp>

namespace padll::stats {

// StatisticEntry default constructor.
StatisticEntry::StatisticEntry() = default;

// StatisticEntry parameterized constructor.
StatisticEntry::StatisticEntry(
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
    ) :
    m_entry_name{name},
    m_timestamp{timestamp},
    m_process_id{process_id},
    m_thread_id{thread_id},
    m_node{node},
    m_descriptor{descriptor},
    m_file_path{file_path},
    m_file_new_path{file_new_path},
    m_offset{offset},
    m_size{size},
    m_result{result} { }

// StatisticEntry parameterized constructor.
StatisticEntry::StatisticEntry(const std::string& name) : m_entry_name{name} { }

// StatisticEntry copy constructor.
StatisticEntry::StatisticEntry(const StatisticEntry& entry) :
    m_entry_name{entry.m_entry_name},
    m_timestamp{entry.m_timestamp},
    m_process_id{entry.m_process_id},
    m_thread_id{entry.m_thread_id},
    m_node{entry.m_node},
    m_descriptor{entry.m_descriptor},
    m_file_path{entry.m_file_path},
    m_file_new_path{entry.m_file_new_path},
    m_offset{entry.m_offset},
    m_size{entry.m_size},
    m_result{entry.m_result} { }

// StatisticEntry default destructor.
StatisticEntry::~StatisticEntry() = default;

// get_entry_name call. Get the name of the StatisticEntry object.
std::string StatisticEntry::get_entry_name() const {
    return this->m_entry_name;
}


// get_operation_counter call. Get the number of registered operations.

// get_result_counter call. Get the number of registered bytes of the result.

// get_error_counter call. Get the number of registered errors.

std::string StatisticEntry::get_timestamp() {
    return this->m_timestamp;
}


std::string StatisticEntry::get_thread_id() {
    return this->m_thread_id;
}


std::string StatisticEntry::get_process_id() {
    return this->m_process_id;
}


std::string StatisticEntry::get_node() {
    return this->m_node;
}


std::string StatisticEntry::get_descriptor() {
    return this->m_descriptor;
}


std::string StatisticEntry::get_file_path() {
    return this->m_file_path;
}


std::string StatisticEntry::get_file_new_path() {
    return this->m_file_new_path;
}


std::string StatisticEntry::get_offset() {
    return this->m_offset;
}


std::string StatisticEntry::get_size() {
    return this->m_size;
}


std::string StatisticEntry::get_result() {
    return this->m_result;
}


// get_bypass_counter call. Get the number of registered bypassed operations.

// increment_operation_counter call. Increments the number of operations.

// increment_byte_counter call. Increments the number of bytes.

// increment_error_counter call. Increments the number of errors.

// increment_bypass_counter call. Increments the number of bypass operations.

void StatisticEntry::set_timestamp(std::string timestamp) {
    this->m_timestamp = timestamp;
}


void StatisticEntry::set_thread_id(std::string thread_id) {
    // lock_guard over mutex
    this->m_thread_id = thread_id;
}


void StatisticEntry::set_process_id(std::string process_id) {
    // lock_guard over mutex
    this->m_process_id = process_id;
}


void StatisticEntry::set_offset(std::string offset) {
    // lock_guard over mutex
    this->m_offset = offset;
}


// to_string call. Generate a string-based format of the contents of the StatisticEntry object.
std::string StatisticEntry::to_string() {
    // lock_guard over mutex

    // TODO: use fmtlib/fmt for easier and faster formatting
    char stream[1000];
    std::sprintf(stream,
                 "%1s,%1s,%1s,%1s,%1s,%1s,%1s,%1s,%1s,%1s,%1s",
                 this->m_entry_name.c_str(),
                 this->m_timestamp.c_str(),
                 this->m_thread_id.c_str(),
                 this->m_process_id.c_str(),
                 this->m_node.c_str(),
                 this->m_descriptor.c_str(),
                 this->m_file_path.c_str(),
                 this->m_file_new_path.c_str(),
                 this->m_offset.c_str(),
                 this->m_size.c_str(),
                 this->m_result.c_str()
                 );

    return { stream };
}


} // namespace padll::stats
