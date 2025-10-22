/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#ifndef PADLL_STATISTICS_H
#define PADLL_STATISTICS_H

#include <fcntl.h>
#include <iostream>
#include <padll/library_headers/libc_enums.hpp>
#include <padll/statistics/statistic_entry.hpp>
#include <padll/third_party/tabulate.hpp>
#include <padll/statistics/buffered_writer.hpp>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <vector>
#include <list>
#include <thread>

using namespace padll::headers;
using namespace tabulate;

namespace padll::stats {

/**
 * Statistics class.
 * This class keeps track of all statistics entries of a given category.
 */
class Statistics {

private:
    buffered_writer::BufferedWriter buffered_writer;

public:

    /**
     * Statistics default constructor.
     */
    Statistics();

    /**
     * Statistics default destructor.
     */
    ~Statistics();

    void flushBufferedWriter();


    void update_statistic_entry(
        std::string&    operation_type,
        std::string     timestamp,
        std::string     thread_id,
        std::string     process_id,
        std::string     node,
        std::string     descriptor,
        std::string     file_path,
        std::string     file_new_path,
        std::string     offset,
        std::string     size,
        std::string     result
        );



};
} // namespace padll::stats

#endif // PADLL_STATISTICS_H
