import winappdbg,log

class Process():
    def __init__(self):
        self.logger = log.log()
    
    def getProcess(self):
        system = winappdbg.System()

        for process in system:
            print process.get_pid(), process.get_filename() 
            '''
            try:
                hProcess = process.open_handle( winappdbg.win32.PROCESS_VM_READ |
                                            winappdbg.win32.PROCESS_QUERY_INFORMATION )

                print hProcess
                
                #a,b,c,d =  win32.kernel32.GetProcessTimes(hProcess)
                #print 'aaaaaaaaaaaaaaa',a.wYear
            except:
                
                raise
            '''        

    def getProcess2(self):
        import win32process,win32api,win32con,os

        p = {}
        p['total'] = 0
        total = 0


        procs = win32process.EnumProcesses()
        for pid in procs:
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
            except Exception as myException:
                self.logger.error(myException)
                handle = None

            if handle:
                try:
                    executablePath = win32process.GetModuleFileNameEx(handle, 0)
                    filename = os.path.basename(executablePath)
                    ptimes = win32process.GetProcessTimes(handle)
                    meminfo = win32process.GetProcessMemoryInfo(handle)
                    pagefile = meminfo['PagefileUsage']/(1024*1024)
                    workset = meminfo['WorkingSetSize']/(1024*1024)
                    p[str(pid)] = (ptimes['UserTime'],ptimes['KernelTime'],pagefile,workset,filename,executablePath)
                    
                    total += float(ptimes['UserTime'])  + float(ptimes['KernelTime'])

                    handle.Close()
                    
                except Exception as myException:
                    self.logger.error(myException)
                    

        p['total'] = total
        
        return p        

if __name__ == '__main__':
    proc = Process()
    print proc.getProcess()