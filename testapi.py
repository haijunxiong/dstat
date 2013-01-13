
import ctypes
from ctypes.wintypes import *
import datetime

PDWORD = ctypes.POINTER(DWORD)
POINTER     = ctypes.POINTER
Structure   = ctypes.Structure

# typedef struct _FILETIME {
#    DWORD dwLowDateTime;
#    DWORD dwHighDateTime;
# } FILETIME, *PFILETIME;
class FILETIME(Structure):
    _fields_ = [
        ('dwLowDateTime',       DWORD),
        ('dwHighDateTime',      DWORD),
    ]

LPFILETIME = POINTER(FILETIME)

class SYSTEMTIME(Structure):
    _fields_ = [
        ('wYear',           WORD),
        ('wMonth',          WORD),
        ('wDayOfWeek',      WORD),
        ('wDay',            WORD),
        ('wHour',           WORD),
        ('wMinute',         WORD),
        ('wSecond',         WORD),
        ('wMilliseconds',   WORD),
    ]
LPSYSTEMTIME = POINTER(SYSTEMTIME)

# Map size_t to SIZE_T
try:
    SIZE_T  = ctypes.c_size_t
#    SSIZE_T = ctypes.c_ssize_t
except AttributeError:
    # Size of a pointer
    SIZE_T  = {1:BYTE, 2:WORD, 4:DWORD, 8:QWORD}[sizeof(LPVOID)]
    #SSIZE_T = {1:SBYTE, 2:SWORD, 4:SDWORD, 8:SQWORD}[sizeof(LPVOID)]

PSIZE_T     = POINTER(SIZE_T)


class PROCESS_MEMORY_COUNTERS(Structure):
    _fields_ = [
        ('cb',                          DWORD),
        ('PageFaultCount',              DWORD),
        ('PeakWorkingSetSize',          SIZE_T),
        ('WorkingSetSize',              SIZE_T),
        ('QuotaPeakPagedPoolUsage',     SIZE_T),
        ('QuotaPagedPoolUsage',         SIZE_T),
        ('QuotaPeakNonPagedPoolUsage',  SIZE_T),
        ('QuotaNonPagedPoolUsage',      SIZE_T),
        ('PagefileUsage',               SIZE_T),
        ('PeakPagefileUsage',           SIZE_T)
    ]

LPPROCESS_MEMORY_COUNTERS = POINTER(PROCESS_MEMORY_COUNTERS)


ERROR_INSUFFICIENT_BUFFER           = 122
MAX_PATH = 260

# Invalid handle value is -1 casted to void pointer.
try:
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value #-1 #0xFFFFFFFF
except TypeError:
    if sizeof(ctypes.c_void_p) == 4:
        INVALID_HANDLE_VALUE = 0xFFFFFFFF
    elif sizeof(ctypes.c_void_p) == 8:
        INVALID_HANDLE_VALUE = 0xFFFFFFFFFFFFFFFF
    else:
        raise



class Process():
    def __init__(self,dwProcessId):
        self.hProcess = None
        self.dwProcessId = dwProcessId
    
    def GetDateTimeFromSystemTime(self,systemTime):

        return datetime.datetime(systemTime.wYear,systemTime.wMonth,systemTime.wDay,systemTime.wHour,systemTime.wMinute,systemTime.wSecond,systemTime.wMilliseconds)



    def open_handle(self, dwDesiredAccess):
        _OpenProcess = ctypes.windll.kernel32.OpenProcess
        _OpenProcess.argtypes = [DWORD, BOOL, DWORD]
        _OpenProcess.restype  = HANDLE
        
        hProcess = _OpenProcess(dwDesiredAccess, 0, self.dwProcessId)

        try:
            self.close_handle()
        except Exception, e:
            #warnings.warn("Failed to close process handle: %s" % traceback.format_exc())
            self.RaiseIfZero(e)

        self.hProcess = hProcess

    def close_handle(self):
        _CloseHandle = ctypes.windll.kernel32.CloseHandle
        _CloseHandle.argtypes = [HANDLE]
        _CloseHandle.restype  = bool
        _CloseHandle.errcheck = self.RaiseIfZero
               
        try:
            if hasattr(self.hProcess, 'close'):
                self.hProcess.close()
            elif self.hProcess not in (None, INVALID_HANDLE_VALUE):
                _CloseHandle(self.hProcess)
        finally:
            self.hProcess = None

        
    def get_handle(self, dwDesiredAccess):
        if self.hProcess in (None, INVALID_HANDLE_VALUE):
            self.open_handle(dwDesiredAccess)
        else:
            dwAccess = self.hProcess.dwAccess
            if (dwAccess | dwDesiredAccess) != dwAccess:
                self.open_handle(dwAccess | dwDesiredAccess)
        return self.hProcess
            

    def RaiseIfZero(self, result, func = None, arguments = ()):
    
        if not result:
            raise ctypes.WinError()
        
        return result    

    def GetProcessMemoryInfo(self):
        _GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
        _GetProcessMemoryInfo.argtypes = [HANDLE, LPPROCESS_MEMORY_COUNTERS, DWORD]
        _GetProcessMemoryInfo.restype  = bool
        _GetProcessMemoryInfo.errcheck = self.RaiseIfZero

        MemInfo = PROCESS_MEMORY_COUNTERS()
        dwSize = ctypes.sizeof(MemInfo)

        _GetProcessMemoryInfo(self.hProcess,ctypes.byref(MemInfo),dwSize)

        return MemInfo

    def GetProcessTimes(self):
        _GetProcessTimes = ctypes.windll.kernel32.GetProcessTimes
        _GetProcessTimes.argtypes = [HANDLE, LPFILETIME, LPFILETIME, LPFILETIME, LPFILETIME]
        _GetProcessTimes.restype  = bool
        _GetProcessTimes.errcheck = self.RaiseIfZero


        CreationTime = FILETIME()
        ExitTime     = FILETIME()
        KernelTime   = FILETIME()
        UserTime     = FILETIME()

        _GetProcessTimes(self.hProcess, ctypes.byref(CreationTime), ctypes.byref(ExitTime), ctypes.byref(KernelTime), ctypes.byref(UserTime))

    ##    CreationTime = CreationTime.dwLowDateTime + (CreationTime.dwHighDateTime << 32)
    ##    ExitTime     = ExitTime.dwLowDateTime     + (ExitTime.dwHighDateTime     << 32)
        KernelTime   = KernelTime.dwLowDateTime   + (KernelTime.dwHighDateTime   << 32)
        UserTime     = UserTime.dwLowDateTime     + (UserTime.dwHighDateTime     << 32)

        CreationTime = self.FileTimeToSystemTime(CreationTime)
        ExitTime     = self.FileTimeToSystemTime(ExitTime)

        return (CreationTime, ExitTime, KernelTime, UserTime)    

    def FileTimeToSystemTime(self,lpFileTime):
        _FileTimeToSystemTime = ctypes.windll.kernel32.FileTimeToSystemTime
        _FileTimeToSystemTime.argtypes = [LPFILETIME, LPSYSTEMTIME]
        _FileTimeToSystemTime.restype  = bool
        _FileTimeToSystemTime.errcheck = self.RaiseIfZero

        if isinstance(lpFileTime, FILETIME):
            FileTime = lpFileTime
        else:
            FileTime = FILETIME()
            FileTime.dwLowDateTime  = lpFileTime & 0xFFFFFFFF
            FileTime.dwHighDateTime = lpFileTime >> 32
        SystemTime = SYSTEMTIME()
        _FileTimeToSystemTime(ctypes.byref(FileTime), ctypes.byref(SystemTime))
        return SystemTime

    # void WINAPI GetSystemTimeAsFileTime(
    #   __out  LPFILETIME lpSystemTimeAsFileTime
    # );
    def GetSystemTimeAsFileTime(self):
        _GetSystemTimeAsFileTime = ctypes.windll.kernel32.GetSystemTimeAsFileTime
        _GetSystemTimeAsFileTime.argtypes = [LPFILETIME]
        _GetSystemTimeAsFileTime.restype  = None

        FileTime = FILETIME()
        _GetSystemTimeAsFileTime(ctypes.byref(FileTime))
        return FileTime
    def GetSystemTimes(self):
        _GetSystemTime = ctypes.windll.kernel32.GetSystemTimes
        _GetSystemTime.argtypes = [LPFILETIME, LPFILETIME,LPFILETIME]
        _GetSystemTime.restype  = bool
        _GetSystemTime.errcheck = self.RaiseIfZero
        
        IdleTime = FILETIME()
        KernelTime = FILETIME()
        UserTime = FILETIME()


        _GetSystemTime(ctypes.byref(IdleTime),ctypes.byref(KernelTime),ctypes.byref(UserTime))
        
        IdleTime = IdleTime.dwHighDateTime << 32 | IdleTime.dwLowDateTime
        KernelTime = KernelTime.dwHighDateTime << 32 | KernelTime.dwLowDateTime
        UserTime = UserTime.dwHighDateTime << 32 | UserTime.dwLowDateTime
                

        return (IdleTime, KernelTime, UserTime)  

    # DWORD WINAPI GetLastError(void);
    def GetLastError(self):
        _GetLastError = ctypes.windll.kernel32.GetLastError
        _GetLastError.argtypes = []
        _GetLastError.restype  = DWORD
        return _GetLastError()

    def GetFileName(self):

        name = None

        if not name:
            try:
                hProcess = self.get_handle(PROCESS_QUERY_LIMITED_INFORMATION)
                name = self.QueryFullProcessImageName(hProcess)
            except (AttributeError, WindowsError):
##                traceback.print_exc()                           # XXX DEBUG
                name = None

        # Method 3: GetProcessImageFileName()
        #
        # Not implemented until Windows XP.
        # For more info see:
        # https://voidnish.wordpress.com/2005/06/20/getprocessimagefilenamequerydosdevice-trivia/
        if not name:
            try:
                hProcess = self.get_handle(win32.PROCESS_QUERY_INFORMATION)
                name = win32.GetProcessImageFileName(hProcess)
                if name:
                    name = PathOperations.native_to_win32_pathname(name)
                else:
                    name = None
            except (AttributeError, WindowsError):
##                traceback.print_exc()                           # XXX DEBUG
                if not name:
                    name = None

        # Method 4: GetModuleFileNameEx()
        # Not implemented until Windows 2000.
        #
        # May be spoofed by malware, since this information resides
        # in usermode space (see http://www.ragestorm.net/blogs/?p=163).
        if not name:
            try:
                hProcess = self.get_handle( win32.PROCESS_VM_READ |
                                            win32.PROCESS_QUERY_INFORMATION )
                try:
                    name = win32.GetModuleFileNameEx(hProcess)
                except WindowsError:
##                    traceback.print_exc()                       # XXX DEBUG
                    name = win32.GetModuleFileNameEx(
                                            hProcess, self.get_image_base())
                if name:
                    name = PathOperations.native_to_win32_pathname(name)
                else:
                    name = None
            except (AttributeError, WindowsError):
##                traceback.print_exc()                           # XXX DEBUG
                if not name:
                    name = None

        return name

    def QueryFullProcessImageName(self, dwFlags = 0):
        _QueryFullProcessImageNameW = ctypes.windll.kernel32.QueryFullProcessImageNameW
        _QueryFullProcessImageNameW.argtypes = [HANDLE, DWORD, LPWSTR, PDWORD]
        _QueryFullProcessImageNameW.restype  = bool

        dwSize = MAX_PATH
        while 1:
            lpdwSize = DWORD(dwSize)
            lpExeName = ctypes.create_unicode_buffer('', lpdwSize.value + 1)
            success = _QueryFullProcessImageNameW(hProcess, dwFlags, lpExeName, ctypes.byref(lpdwSize))
            if success and 0 < lpdwSize.value < dwSize:
                break
            error = GetLastError()
            if error != ERROR_INSUFFICIENT_BUFFER:
                raise ctypes.WinError(error)
            dwSize = dwSize + 256
            if dwSize > 0x1000:
                # this prevents an infinite loop in Windows 2008 when the path has spaces,
                # see http://msdn.microsoft.com/en-us/library/ms684919(VS.85).aspx#4
                raise ctypes.WinError(error)
        return lpExeName.value

    

    def QueryFullProcessImageName(self):
        _QueryFullProcessImageNameW = ctypes.windll.kernel32.QueryFullProcessImageNameW 
        _QueryFullProcessImageNameW.argtypes = [HANDLE, DWORD, LPWSTR, PDWORD] 
        _QueryFullProcessImageNameW.restype  = bool 

        dwFlags = 0
        dwSize = MAX_PATH 

        while 1: 
            lpdwSize = DWORD(dwSize) 
            lpExeName = ctypes.create_unicode_buffer('', lpdwSize.value + 1)
            
            success = _QueryFullProcessImageNameW(self.hProcess, dwFlags, lpExeName, ctypes.byref(lpdwSize)) 
            
            if success and 0 < lpdwSize.value < dwSize: 
                break 

            error = self.GetLastError() 
            if error != ERROR_INSUFFICIENT_BUFFER: 
                raise ctypes.WinError(error) 
            dwSize = dwSize + 256 
            if dwSize > 0x1000: 
                  # this prevents an infinite loop in Windows 2008 when the path has spaces, 
                  # see http://msdn.microsoft.com/en-us/library/ms684919(VS.85).aspx#4 
                raise ctypes.WinError(error) 
          
        return lpExeName.value 



if __name__ == '__main__':
    import time

    api = Process(7596)
    idleTime, kernelTime, userTime = api.GetSystemTimes()
    print idleTime, kernelTime, userTime

    #print 'idletime', long(idleTime.dwHighDateTime) << 32 +  long(idleTime.dwLowDateTime)

    #handle = api.open_handle(0x1000)
    #print api.QueryFullProcessImageName()

    #a,b,c,d = api.GetProcessTimes()
    #print a.wYear
    
    #meminfo = api.GetProcessMemoryInfo()
    #print meminfo.PagefileUsage / (1024*1024),meminfo.WorkingSetSize/ (1024*1024)
    api.close_handle()
    #handle.Close()
