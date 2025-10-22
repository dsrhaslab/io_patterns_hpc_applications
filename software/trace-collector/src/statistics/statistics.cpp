/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#include "padll/statistics/statistic_entry.hpp"
#include <fcntl.h>
#include <padll/statistics/statistics.hpp>
#include <string>
#include <thread>

namespace padll::stats {

// Statistics default constructor.
Statistics::Statistics() = default;

// Statistics default destructor.
Statistics::~Statistics() = default;

// update_statistics_entry call. (...)
void Statistics::update_statistic_entry(std::string&    operation_type,
                                        std::string     timestamp,
                                        std::string     thread_id,
                                        std::string     process_id,
                                        std::string     node,
                                        std::string     descriptor,
                                        std::string     file_path,
                                        std::string     new_path,
                                        std::string     offset,
                                        std::string     size,
                                        std::string     result) {
    // calculate the operation's position (index) in the statistics container
    // int position = operation_type % this->m_stats_size;

    //std::cout << operation_type << "\n" << std::endl;

    StatisticEntry stat(operation_type, timestamp, process_id, thread_id, node, descriptor, file_path, new_path, offset, size, result);
    this->buffered_writer.bufferedWrite(&stat);
    // this->m_statistic_entries_list.push_back(stat);
}


void Statistics::flushBufferedWriter() {
    this->buffered_writer.flushAllBuffers();
}

} // namespace padll::stats
