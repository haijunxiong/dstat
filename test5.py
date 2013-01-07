import os

def getProcess():
    import win32process,win32api,win32con

    p = {}

    procs = win32process.EnumProcesses()
    for pid in procs:
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
        except:
            handle = None

        exe = None
        if handle:
            try:
                executablePath = win32process.GetModuleFileNameEx(handle, 0)
                filename = os.path.basename(executablePath)
                ptimes = win32process.GetProcessTimes(handle)
                meminfo = win32process.GetProcessMemoryInfo(handle)
                pagefile = meminfo['PagefileUsage']/(1024*1024)
                workset = meminfo['WorkingSetSize']/(1024*1024)
                p[pid] = (ptimes['UserTime'],ptimes['KernelTime'],pagefile,workset,filename,executablePath)
                
                
            except:
                pass
        

        if handle:
            handle.Close()
    return p        

if __name__ == '__main__':
    print getProcess()
    print getProcess()