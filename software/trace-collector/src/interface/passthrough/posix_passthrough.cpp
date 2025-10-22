/**
 *   Written by Ricardo Macedo.
 *   Copyright (c) 2021-2023 INESC TEC.
 **/

#include <padll/interface/passthrough/posix_passthrough.hpp>
#include <string>
#include <utility>
#include <thread>
#include <sstream>
#include <unistd.h>
#include <padll/options/options.hpp>
#include <sys/utsname.h>

namespace padll::interface::passthrough {

// PosixPassthrough default constructor.
PosixPassthrough::PosixPassthrough() :
    m_log{std::make_shared<Log> (option_default_enable_debug_level,
                                 option_default_enable_debug_with_ld_preload,
                                 std::string { option_default_log_path })} {
    #if OPTION_WITH_LOGGING
    // create logging message
    std::stringstream stream;
    stream << "PosixPassthrough default constructor ";
    stream << "(" << static_cast<void *> (this->m_log.get()) << ")";
    this->m_log->log_info(stream.str());
    #endif

    // initialize library handle pointer.
    this->initialize();
}


// PosixPassthrough explicit parameterized constructor.
PosixPassthrough::PosixPassthrough(const std::string& lib_name, std::shared_ptr<Log> log_ptr) :
    m_lib_name{lib_name},
    m_log{log_ptr} {
    
    #if OPTION_WITH_LOGGING
    // create logging message
    std::stringstream stream;
    stream << "PosixPassthrough parameterized constructor ";
    stream << "(" << static_cast<void *> (this->m_log.get()) << ")";
    this->m_log->log_info(stream.str());
    #endif

    // initialize library handle pointer.
    this->initialize();
}


// PosixPassthrough default destructor.
PosixPassthrough::~PosixPassthrough() {

    #if OPTION_WITH_LOGGING
    // create logging message
    this->m_log->log_info("PosixPassthrough default destructor.");
    #endif

    this->stats.flushBufferedWriter();


    // validate if library handle is valid and close dynamic linking.
    // It decrements the reference count on the dynamically loaded shared object, referred to
    // by handle m_lib_handle. If the reference count drops to zero, then the object is
    // unloaded. All shared objects that were automatically loaded when dlopen () was invoked
    // on the object referred to by handle are recursively closed in the same manner.

    int close_failed = ::dlclose(this->m_lib_handle);
    if ((this->m_lib_handle != nullptr) && close_failed) {
        #if OPTION_WITH_LOGGING
        this->m_log->log_error("PosixPassthrough::Error while closing dynamic link.\n");
        #endif
    }
}


std::string PosixPassthrough::getCurrentTimestamp() {

    // Get current time
    auto currentTime = std::chrono::system_clock::now();

    // Get the duration since the epoch
    auto durationSinceEpoch = currentTime.time_since_epoch();

    // Convert the duration to seconds
    long long epochNanoTimeSeconds = std::chrono::duration_cast<std::chrono::nanoseconds>(durationSinceEpoch).count();

    // Convert the epoch time to a string
    return std::to_string(epochNanoTimeSeconds);

}



std::string PosixPassthrough::threadIdToString(std::thread::id thread_id) {
    std::stringstream ss;
    ss << thread_id;
    return ss.str();
}


std::string PosixPassthrough::pidToString(pid_t pid) {
    return std::to_string(static_cast<int>(pid));
}


// Function to get the current node name.
std::string PosixPassthrough::get_current_node() {
    struct utsname buffer;

    // Retrieve system information
    if (uname(&buffer) != 0) {
        return std::string("Error: ") + strerror(errno);
    }

    return std::string(buffer.nodename);
}


// dlopen_library_handle call.
bool PosixPassthrough::dlopen_library_handle() {
    // unique_lock over mutex
    std::unique_lock lock(this->m_lock);
    // Dynamic loading of the libc library (referred to as 'libc.so.6').
    // loads the dynamic shared object (shared library) file named by the null-terminated string
    // filename and returns an opaque "handle" for the loaded object.
    this->m_lib_handle = ::dlopen(this->m_lib_name.data(), RTLD_LAZY);

    // return true if the m_lib_handle is valid, and false otherwise.
    return(this->m_lib_handle != nullptr);
}


// initialize call.
void PosixPassthrough::initialize() {
    // assign pointer to m_lib_handle, and validate pointer
    if (!this->dlopen_library_handle()) {
        #if OPTION_WITH_LOGGING
        this->m_log->log_error("PosixPassthrough::Error while dlopen'ing "
                               + (this->m_lib_name.empty() ? "<undefined lib>" : this->m_lib_name) + ".");
        #endif
        return;
    }
}


// set_statistic_collection call.


// passthrough_posix_read call.
ssize_t PosixPassthrough::passthrough_posix_read(int fd, void *buf, size_t counter) {
    ssize_t result = ((libc_read_t)dlsym(RTLD_NEXT, "read")) (fd, buf, counter);

    std::string operation("read");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_write call.
ssize_t PosixPassthrough::passthrough_posix_write(int fd, const void *buf, size_t counter) {
    ssize_t result = ((libc_write_t)dlsym(RTLD_NEXT, "write")) (fd, buf, counter);

    std::string operation("write");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_pread call.
ssize_t PosixPassthrough::passthrough_posix_pread(int fd, void *buf, size_t counter, off_t offset) {
    ssize_t result = ((libc_pread_t)dlsym(RTLD_NEXT, "pread")) (fd, buf, counter, offset);

    std::string operation("pread");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset_str = std::to_string(offset);

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset_str,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_pwrite call.
ssize_t
PosixPassthrough::passthrough_posix_pwrite(int fd, const void *buf, size_t counter, off_t offset) {
    ssize_t result = ((libc_pwrite_t)dlsym(RTLD_NEXT, "pwrite")) (fd, buf, counter, offset);

    std::string operation("pwrite");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset_str = std::to_string(offset);

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset_str,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;
}


// passthrough_posix_pread64 call.
#if defined(__USE_LARGEFILE64)
ssize_t
PosixPassthrough::passthrough_posix_pread64(int fd, void *buf, size_t counter, off64_t offset) {
    ssize_t result = ((libc_pread64_t)dlsym(RTLD_NEXT, "pread64")) (fd, buf, counter, offset);

    std::string operation("pread64");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset_str = std::to_string(offset);

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset_str,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;

}
#endif

// passthrough_posix_pwrite64 call.
#if defined(__USE_LARGEFILE64)
ssize_t PosixPassthrough::passthrough_posix_pwrite64(int         fd,
                                                     const void *buf,
                                                     size_t      counter,
                                                     off64_t     offset) {
    ssize_t result = ((libc_pwrite64_t)dlsym(RTLD_NEXT, "pwrite64")) (fd, buf, counter, offset);

    std::string operation("pwrite64");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset_str = std::to_string(offset);

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset_str,
        std::to_string(counter),
        std::to_string(result)
        );

    return result;

}
#endif

// pass_through_posix_mmap call.
void * PosixPassthrough::passthrough_posix_mmap(void * addr,
                                                size_t length,
                                                int    prot,
                                                int    flags,
                                                int    fd,
                                                off_t  offset) {
    void *result = ((libc_mmap_t)dlsym(RTLD_NEXT, "mmap")) (addr, length, prot, flags, fd, offset);
    
    std::string operation("mmap");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset_str = std::to_string(offset);
    
    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset_str,
        std::to_string(length),
        result ? std::to_string(reinterpret_cast<uintptr_t>(result)) : "nullptr"
    );
    

    return result;

}


// pass_through_posix_munmap call.
int PosixPassthrough::passthrough_posix_munmap(void *addr, size_t length) {
    int result = ((libc_munmap_t)dlsym(RTLD_NEXT, "munmap")) (addr, length);

    std::string operation("munmap");
    std::string fd = "";
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        file_path,
        new_path,
        offset,
        std::to_string(length),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_open call.
int PosixPassthrough::passthrough_posix_open(const char *path, int flags, mode_t mode) {
    int result = ((libc_open_variadic_t)dlsym(RTLD_NEXT, "open")) (path, flags, mode);

    std::string operation("open_variadic");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;
}


// passthrough_posix_open call.
int PosixPassthrough::passthrough_posix_open(const char *path, int flags) {
    int result = ((libc_open_t)dlsym(RTLD_NEXT, "open")) (path, flags);

    std::string operation("open");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;


    return result;
}


// passthrough_posix_creat call.
int PosixPassthrough::passthrough_posix_creat(const char *path, mode_t mode) {
    int result = ((libc_creat_t)dlsym(RTLD_NEXT, "creat")) (path, mode);

    std::string operation("creat");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_creat64 call.
int PosixPassthrough::passthrough_posix_creat64(const char *path, mode_t mode) {
    int result = ((libc_creat64_t)dlsym(RTLD_NEXT, "creat64")) (path, mode);

    std::string operation("creat64");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_openat call.
int PosixPassthrough::passthrough_posix_openat(int dirfd, const char *path, int flags, mode_t mode) {
    int result = ((libc_openat_variadic_t)dlsym(RTLD_NEXT, "openat")) (dirfd, path, flags, mode);

    std::string operation("openat_variadic");
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(dirfd),
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_openat call.
int PosixPassthrough::passthrough_posix_openat(int dirfd, const char *path, int flags) {
    int result = ((libc_openat_t)dlsym(RTLD_NEXT, "openat")) (dirfd, path, flags);

    std::string operation("openat");
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(dirfd),
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_open64 call.
int PosixPassthrough::passthrough_posix_open64(const char *path, int flags, mode_t mode) {
    int result = ((libc_open64_variadic_t)dlsym(RTLD_NEXT, "open64")) (path, flags, mode);

    std::string operation("open64_variadic");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_open64 call.
int PosixPassthrough::passthrough_posix_open64(const char *path, int flags) {
    int result = ((libc_open64_t)dlsym(RTLD_NEXT, "open64")) (path, flags);

    std::string operation("open64");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_close call.
int PosixPassthrough::passthrough_posix_close(int fd) {
    int result = ((libc_close_t)dlsym(RTLD_NEXT, "close")) (fd);

    std::string operation("close");
    std::string new_path = "";
    std::string file_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_sync call.
void PosixPassthrough::passthrough_posix_sync() {
    ((libc_sync_t)dlsym(RTLD_NEXT, "sync")) ();

    std::string operation("sync");
    std::string fd = "";
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        fd,
        file_path,
        new_path,
        offset,
        counter,
        this->get_current_node(),
        ""
        );
}


// passthrough_posix_statfs call.
int PosixPassthrough::passthrough_posix_statfs(const char *path, struct statfs *buf) {
    int result = ((libc_statfs_t)dlsym(RTLD_NEXT, "statfs")) (path, buf);

    // update statistic entry
    std::string operation("statfs");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;
}


// passthrough_posix_fstatfs call.
int PosixPassthrough::passthrough_posix_fstatfs(int fd, struct statfs *buf) {
    int result = ((libc_fstatfs_t)dlsym(RTLD_NEXT, "fstatfs")) (fd, buf);


    // update statistic entry
    std::string operation("fstatfs");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_statfs64 call.
int PosixPassthrough::passthrough_posix_statfs64(const char *path, struct statfs64 *buf) {
    int result = ((libc_statfs64_t)dlsym(RTLD_NEXT, "statfs64")) (path, buf);

    // update statistic entry
    std::string operation("statfs64");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_fstatfs64 call.
int PosixPassthrough::passthrough_posix_fstatfs64(int fd, struct statfs64 *buf) {
    int result = ((libc_fstatfs64_t)dlsym(RTLD_NEXT, "fstatfs64")) (fd, buf);

    // update statistic entry
    std::string operation("fstatfs64");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_unlink call.
int PosixPassthrough::passthrough_posix_unlink(const char *old_path) {
    int result = ((libc_unlink_t)dlsym(RTLD_NEXT, "unlink")) (old_path);

    // update statistic entry
    std::string operation("unlink");
    std::string fd = "";
    std::string path_str(old_path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_unlinkat call.
int PosixPassthrough::passthrough_posix_unlinkat(int dirfd, const char *pathname, int flags) {
    int result = ((libc_unlinkat_t)dlsym(RTLD_NEXT, "unlinkat")) (dirfd, pathname, flags);

    // update statistic entry
    std::string operation("unlinkat");
    std::string path_str(pathname);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(dirfd),
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_rename call.
int PosixPassthrough::passthrough_posix_rename(const char *old_path, const char *new_path) {
    int result = ((libc_rename_t)dlsym(RTLD_NEXT, "rename")) (old_path, new_path);

    // update statistic entry
    std::string operation("rename");
    std::string fd = "";
    std::string path_str(old_path);
    std::string new_path_str(new_path);
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path_str,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_renameat call.
int PosixPassthrough::passthrough_posix_renameat(int         olddirfd,
                                                 const char *old_path,
                                                 int         newdirfd,
                                                 const char *new_path) {
    int result = ((libc_renameat_t)dlsym(RTLD_NEXT, "renameat")) (
        olddirfd,
        old_path,
        newdirfd,
        new_path
        );

    // update statistic entry
    std::string operation("renameat");
    std::string fd = "";
    std::string path_str(old_path);
    std::string new_path_str(new_path);
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path_str,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_fopen call.
FILE * PosixPassthrough::passthrough_posix_fopen(const char *pathname, const char *mode) {
    FILE *result = ((libc_fopen_t)dlsym(RTLD_NEXT, "fopen")) (pathname, mode);

    std::string operation("fopen");
    std::string fd = "";
    std::string path_str(pathname);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    if (result) {
        // File opened successfully
        this->stats.update_statistic_entry(
            operation,
            this->getCurrentTimestamp(),
            this->threadIdToString(std::this_thread::get_id()),
            pidToString(getpid()),
            this->get_current_node(),
            std::to_string(fileno(result)),
            path_str,
            new_path,
            offset,
            counter,
            "file opened"
        );
    } else {
        // File opening failed
        this->stats.update_statistic_entry(
            operation,
            this->getCurrentTimestamp(),
            this->threadIdToString(std::this_thread::get_id()),
            pidToString(getpid()),
            this->get_current_node(),
            fd,
            path_str,
            new_path,
            offset,
            counter,
            strerror(errno)
        );
    }

    return result;

}


// passthrough_posix_fopen64 call.
FILE * PosixPassthrough::passthrough_posix_fopen64(const char *pathname, const char *mode) {
    FILE *result = ((libc_fopen64_t)dlsym(RTLD_NEXT, "fopen64")) (pathname, mode);

    std::string operation("fopen64");
    std::string fd = "";
    std::string path_str(pathname);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    if (result) {
        // File opened successfully
        this->stats.update_statistic_entry(
            operation,
            this->getCurrentTimestamp(),
            this->threadIdToString(std::this_thread::get_id()),
            pidToString(getpid()),
            this->get_current_node(),
            std::to_string(fileno(result)),
            path_str,
            new_path,
            offset,
            counter,
            "file opened"
        );
    } else {
        // File opening failed
        this->stats.update_statistic_entry(
            operation,
            this->getCurrentTimestamp(),
            this->threadIdToString(std::this_thread::get_id()),
            pidToString(getpid()),
            this->get_current_node(),
            fd,
            path_str,
            new_path,
            offset,
            counter,
            strerror(errno)
        );
    }

    return result;

}


// passthrough_posix_fclose call.
int PosixPassthrough::passthrough_posix_fclose(FILE *stream) {
    
    int fd = fileno(stream);
    int result = ((libc_fclose_t)dlsym(RTLD_NEXT, "fclose")) (stream);

    std::string operation("fclose");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_mkdir call.
int PosixPassthrough::passthrough_posix_mkdir(const char *path, mode_t mode) {
    int result = ((libc_mkdir_t)dlsym(RTLD_NEXT, "mkdir")) (path, mode);

    std::string operation("mkdir");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_mkdirat call.
int PosixPassthrough::passthrough_posix_mkdirat(int dirfd, const char *path, mode_t mode) {
    int result = ((libc_mkdirat_t)dlsym(RTLD_NEXT, "mkdirat")) (dirfd, path, mode);

    std::string operation("mkdirat");
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(dirfd),
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_rmdir call.
int PosixPassthrough::passthrough_posix_rmdir(const char *path) {
    int result = ((libc_rmdir_t)dlsym(RTLD_NEXT, "rmdir")) (path);

    std::string operation("rmdir");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_mknod call.
int PosixPassthrough::passthrough_posix_mknod(const char *path, mode_t mode, dev_t dev) {
    int result = ((libc_mknod_t)dlsym(RTLD_NEXT, "mknod")) (path, mode, dev);

    // update statistic entry
    std::string operation("mknod");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_mknodat call.
int PosixPassthrough::passthrough_posix_mknodat(int         dirfd,
                                                const char *path,
                                                mode_t      mode,
                                                dev_t       dev) {
    int result = ((libc_mknodat_t)dlsym(RTLD_NEXT, "mknodat")) (dirfd, path, mode, dev);

    // update statistic entry
    std::string operation("mknodat");
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(dirfd),
        path_str,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_getxattr call.
ssize_t PosixPassthrough::passthrough_posix_getxattr(const char *path,
                                                     const char *name,
                                                     void *      value,
                                                     size_t      size) {
    ssize_t result = ((libc_getxattr_t)dlsym(RTLD_NEXT, "getxattr")) (path, name, value, size);

    // update statistic entry
    std::string operation("getxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_lgetxattr call.
ssize_t PosixPassthrough::passthrough_posix_lgetxattr(const char *path,
                                                      const char *name,
                                                      void *      value,
                                                      size_t      size) {
    ssize_t result = ((libc_lgetxattr_t)dlsym(RTLD_NEXT, "lgetxattr")) (path, name, value, size);

    // update statistic entry
    std::string operation("lgetxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_fgetxattr call.
ssize_t
PosixPassthrough::passthrough_posix_fgetxattr(int fd, const char *name, void *value, size_t size) {
    ssize_t result = ((libc_fgetxattr_t)dlsym(RTLD_NEXT, "fgetxattr")) (fd, name, value, size);

    // update statistic entry
    std::string operation("fgetxattr");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_setxattr call.
int PosixPassthrough::passthrough_posix_setxattr(const char *path,
                                                 const char *name,
                                                 const void *value,
                                                 size_t      size,
                                                 int         flags) {
    int result = ((libc_setxattr_t)dlsym(RTLD_NEXT, "setxattr")) (path, name, value, size, flags);

    // update statistic entry
    std::string operation("setxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";
    
    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_lsetxattr call.
int PosixPassthrough::passthrough_posix_lsetxattr(const char *path,
                                                  const char *name,
                                                  const void *value,
                                                  size_t      size,
                                                  int         flags) {
    int result = ((libc_lsetxattr_t)dlsym(RTLD_NEXT, "lsetxattr")) (
        path,
        name,
        value,
        size,
        flags
        );

    // update statistic entry
    std::string operation("lsetxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_fsetxattr call.
int PosixPassthrough::passthrough_posix_fsetxattr(int         fd,
                                                  const char *name,
                                                  const void *value,
                                                  size_t      size,
                                                  int         flags) {
    int result = ((libc_fsetxattr_t)dlsym(RTLD_NEXT, "fsetxattr")) (
        fd,
        name,
        value,
        size,
        flags
        );

    // update statistic entry
    std::string operation("fsetxattr");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_listxattr call.
ssize_t PosixPassthrough::passthrough_posix_listxattr(const char *path, char *list, size_t size) {
    ssize_t result = ((libc_listxattr_t)dlsym(RTLD_NEXT, "listxattr")) (path, list, size);

    // update statistic entry
    std::string operation("listxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;

}


// passthrough_posix_llistxattr call.
ssize_t PosixPassthrough::passthrough_posix_llistxattr(const char *path, char *list, size_t size) {
    ssize_t result = ((libc_llistxattr_t)dlsym(RTLD_NEXT, "llistxattr")) (path, list, size);

    // update statistic entry
    std::string operation("llistxattr");
    std::string fd = "";
    std::string path_str(path);
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        path_str,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

    return result;


    return result;
}


// passthrough_posix_flistxattr call.
ssize_t PosixPassthrough::passthrough_posix_flistxattr(int fd, char *list, size_t size) {
    ssize_t result = ((libc_flistxattr_t)dlsym(RTLD_NEXT, "flistxattr")) (fd, list, size);

         // update statistic entry
    std::string operation("flistxattr");
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        std::to_string(fd),
        file_path,
        new_path,
        offset,
        std::to_string(size),
        std::to_string(result)
        );

     return result;

}


// passthrough_posix_socket call.
int PosixPassthrough::passthrough_posix_socket(int domain, int type, int protocol) {
    int result = ((libc_socket_t)dlsym(RTLD_NEXT, "socket")) (domain, type, protocol);

         // update statistic entry
    std::string operation("socket");
    std::string fd = "";
    std::string file_path = "";
    std::string new_path = "";
    std::string offset = "";
    std::string counter = "";

    this->stats.update_statistic_entry(
        operation,
        this->getCurrentTimestamp(),
        this->threadIdToString(std::this_thread::get_id()),
        pidToString(getpid()),
        this->get_current_node(),
        fd,
        file_path,
        new_path,
        offset,
        counter,
        std::to_string(result)
        );

     return result;

}


} // namespace padll::interface::passthrough
