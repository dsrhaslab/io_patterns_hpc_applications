#include "padll/statistics/statistic_entry.hpp"
#include <map>
#include <mutex>
#include <string>
#include <vector>

using namespace std;

namespace padll::buffered_writer {
typedef std::vector<padll::stats::StatisticEntry> Buffer;

typedef struct {
    Buffer* buffer;
    int size;
} BufferStruct;

typedef map<string, BufferStruct> BufferMap;

typedef map<string, int> FileMap ;

/**
* BufferedWriter class.
* This class writes statistic_entry's to a file in a buffered manner
* all operations are thread safe
*/
class BufferedWriter {

public:
    /**
      * BufferedWriter default constuctor
      */
    BufferedWriter();
    BufferedWriter(BufferedWriter &&) = delete;
    BufferedWriter(const BufferedWriter &) = delete;
    BufferedWriter &operator=(BufferedWriter &&) = delete;
    BufferedWriter &operator=(const BufferedWriter &) = delete;
    ~BufferedWriter();

    mutex locker;

    /**
      * bufferedWrite 
      * adds statistic_entry to the bufferd controled by the BufferedWriter class
      * @param statistic_entry
      */
    int bufferedWrite(padll::stats::StatisticEntry*);
    /**
      * flushBuffer 
      * writes all entries in the buffer to files
      */
    void flushBuffer(Buffer*, string Pid, string Tid);

    void flushAllBuffers();

private:

    void safeInsert(string Tid, BufferStruct buffer);

    const int maxBufferSize = 10000;
    BufferMap bufferMap;

};}
