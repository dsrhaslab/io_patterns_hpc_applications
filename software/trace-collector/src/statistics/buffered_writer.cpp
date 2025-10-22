#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <fcntl.h>
#include <filesystem>
#include <iostream>
#include <map>
#include <mutex>
#include <ostream>
#include <padll/statistics/buffered_writer.hpp>
#include <string>
#include <sys/stat.h>
#include <system_error>
#include <unistd.h>
#include <utility>
#include <padll/library_headers/libc_headers.hpp>
#include <padll/options/options.hpp>

using namespace padll::headers;


namespace padll::buffered_writer {

BufferedWriter::BufferedWriter() {}


BufferedWriter::~BufferedWriter() {}

int BufferedWriter::bufferedWrite(padll::stats::StatisticEntry *entry) {

    //this works but its possible to allow further paralellism by releasing the lock befor writing
    //the buffer to a file, by taking a copy of it

    string Pid = entry->get_process_id();
    string Tid = entry->get_thread_id();


    BufferMap::iterator bufferValue = this->bufferMap.find(Tid);

    BufferStruct buffer;

    if (bufferValue != bufferMap.end()) {

        buffer = bufferValue->second;

        if (buffer.size + sizeof(*entry) >= options::option_max_buffer_size) {

            this->flushBuffer(buffer.buffer, Pid, Tid);

            // for (auto entry : *buffer.buffer) {
            //     delete entry;
            // }

            buffer.buffer->clear();
            buffer.buffer->push_back(*entry);
            buffer.size = sizeof(*entry);

        } else {

            buffer.size += sizeof(*entry);
            buffer.buffer->push_back(*entry);
            // std::cout << "put entry fo size " << sizeof(entry) << " in buffer\n";

        }

        //update value associated with thread id
        this->bufferMap[Tid] = buffer;

        //this runs only once per thread
        //initialyze the buffer for a new thread
    }else{

        //alocating memory for buffer
        // this buffer is needed for the entire runtime of the program
        buffer.buffer = new Buffer({ *entry });
        buffer.size   = sizeof(*entry);

        //only locking on map entry creation (im considering this a write to the map object)
        // this->locker.lock();
        // this->bufferMap.insert({ Tid, buffer });
        // this->locker.unlock();
        this->safeInsert(Tid, buffer);
    }

    return 0;
}


void BufferedWriter::safeInsert(string Tid, BufferStruct buffer) {
    lock_guard lock { this->locker };
    if (this -> bufferMap.size() == 0){
        map<string,BufferStruct> myMap = {};
        myMap.insert({Tid,buffer});
        this->bufferMap = myMap;
    }
    else{
        this->bufferMap.insert({ Tid, buffer });
    }
}


void BufferedWriter::flushBuffer(Buffer *buffer, string Pid, string Tid) {

    string filename(options::option_default_statistics_report_path);

    int i = 0;

    filename.append(Pid);
    filename.append("_");
    filename.append(Tid);

    //TODO: add header to all files
    int fd = ((libc_open_variadic_t)dlsym(RTLD_NEXT, "open")) (filename.c_str(), O_APPEND | O_CREAT | O_WRONLY, 0666);

    if(fd == -1) std::cout << "error opening log file" + filename + "\n";

    for (auto entry : *buffer) {

        i++;

        std::string output = entry.to_string();
        dprintf(fd, "%s\n", output.c_str());

    }

    #if OPTION_WITH_LOGGING
    printf("flushed %d entries\n", i);
    #endif

}


void BufferedWriter::flushAllBuffers() {

    string Pid = std::to_string(static_cast<int>(getpid()));

    for (auto bufferValue : this->bufferMap) {

        flushBuffer(bufferValue.second.buffer, Pid, bufferValue.first);
        //delete bufferValue.second.buffer; //dealocating buffer at the end of runtime

    }
}


}
