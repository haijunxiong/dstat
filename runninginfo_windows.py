import re,uuid,time,json
import win32pdh, win32pdhutil
import win32process,win32api,win32con,os
import ctypes,winappdbg,winappdbg.win32.kernel32
import log


class dstat:
    def __init__(self):
        self.val = {}

class dstat_counter(dstat):
       
    def __init__(self):
        self.val = {}
        self.logger = log.log()
        self.AppKey = self.getAppKey()
        

    def getAppKey(self):
        import _winreg
        try:
            HKEY_CLASSES_ROOT = 2147483648
            path = 'AppID\{66313316-FECB-4A41-A335-2BB51624CB14}'

            with _winreg.OpenKey(HKEY_CLASSES_ROOT, path, 0, _winreg.KEY_ALL_ACCESS) as key:                            
                value = _winreg.QueryValueEx(key, 'AppKey')
                return str(value[0])    
        except:
            return ''

    def getSystemTimes(self):
        FILETIME = winappdbg.win32.kernel32.FILETIME
        LPFILETIME = winappdbg.win32.kernel32.LPFILETIME

        _GetSystemTime = ctypes.windll.kernel32.GetSystemTimes
        _GetSystemTime.argtypes = [LPFILETIME, LPFILETIME,LPFILETIME]
        _GetSystemTime.restype  = bool
        #_GetSystemTime.errcheck = None
        
        IdleTime = FILETIME()
        KernelTime = FILETIME()
        UserTime = FILETIME()


        _GetSystemTime(ctypes.byref(IdleTime),ctypes.byref(KernelTime),ctypes.byref(UserTime))
        
        IdleTime = IdleTime.dwHighDateTime << 32 | IdleTime.dwLowDateTime
        KernelTime = KernelTime.dwHighDateTime << 32 | KernelTime.dwLowDateTime
        UserTime = UserTime.dwHighDateTime << 32 | UserTime.dwLowDateTime
                

        return (IdleTime, KernelTime, UserTime)  
    
    def openProcess(self,pid):

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        handle = None

        try:
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
        except:
            handle = None

        if not handle:
            try:  
                handle = win32api.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
            except:
                handle = None

        return handle   

    def CloseHandle(self,handle):
        
        try:
            if handle:
                win32api.CloseHandle(handle)    
                
                if hasattr(handle, 'close'):
                    handle.close()    
        except:
            pass        
        finally:
            handle = None
  
    def getProcess(self):

        p = {}

        try:

            systime = self.getSystemTimes()

            p['total'] = systime[1] + systime[2]

            procs = win32process.EnumProcesses()
            for pid in procs:

                if pid ==0: continue

                handle = self.openProcess(pid)

                if handle:
                    try:
                        try:
                            executablePath = win32process.GetModuleFileNameEx(handle, 0)
                        except:
                            executablePath = None
                        
                        if not executablePath:
                            winapp = winappdbg.Process(pid)
                            executablePath = winapp.get_filename()

                        filename = os.path.basename(executablePath)

                        if filename.find('TMatrix') ==0 :
                            continue

                        ptimes = win32process.GetProcessTimes(handle)
                        meminfo = win32process.GetProcessMemoryInfo(handle)
                        pagefile = meminfo['PagefileUsage']/(1024*1024)
                        workset = meminfo['WorkingSetSize']/(1024*1024)
                        p[str(pid)] = (ptimes['UserTime'],ptimes['KernelTime'],pagefile,workset,filename,executablePath)
                        
                    except Exception as myException:
                        self.logger.error(myException)
                    finally:    
                        self.CloseHandle(handle)

        except Exception as  myException:
            self.logger.error(myException)      
        

        return p        


    def getProcessFromWmi(self):
        import wmi
        w = wmi.WMI()
        p = {}
        p['total'] = 0
        total = 0

        try:
          
            process = w.Win32_Process(['processid','KernelModeTime','Name','ExecutablePath','privatepagecount','usermodetime','workingsetsize'])
            for proc in process:
                p[str(proc.ProcessId)] = (float(proc.UserModeTime),float(proc.KernelModeTime),float(proc.privatepagecount)/(1024*1024),float(proc.workingsetsize)/(1024*1024),proc.Name,proc.ExecutablePath)
                total +=    float(proc.UserModeTime)  + float(proc.KernelModeTime)
                p['total'] = total
        except:
            pass

        return p

    def getDiskSize(self):
        import win32file

        try:

            freespace = 0
            disksize = 0

            drives=[]
            sign=win32file.GetLogicalDrives()
            drive_all=["A:\\","B:\\","C:\\","D:\\","E:\\","F:\\","G:\\","H:\\","I:\\","J:\\","K:\\","L:\\","M:\\","N:\\","O:\\","P:\\","Q:\\","R:\\","S:\\","T:\\","U:\\","V:\\","W:\\","X:\\","Y:\\","Z:\\"]
            for i in range(25):
                if (sign & 1<<i):
                    if win32file.GetDriveType(drive_all[i]) == 3:
                        space = win32file.GetDiskFreeSpace(drive_all[i])
                        #print space
                        freespace += space[0]*space[1]*space[2]
                        disksize += space[0]*space[1]*space[3]

            return (freespace,disksize)
        
        except Exception as  myException:
            self.logger.error(myException)   
            return (0,0) 

    def getDiskSizeFromWmi(self):
        import wmi
        w = wmi.WMI()
        freespace = 0
        disksize = 0

        try:
            fixed_disks = w.Win32_LogicalDisk (DriveType=3)
            for fdisk in fixed_disks:
                freespace += float(fdisk.freespace)
                disksize += float(fdisk.size)
        except:
            pass

        return (freespace,disksize)

    def extract(self):
        def getQueryValue(data,key):
            if key in data:
                return data[key]
            else:
                return None

        paths = [   
                    ('cpu-total','Processor','_Total','% Processor Time'),
                    ('cpu-us','Processor','_Total','% User Time'),
                    ('cpu-sy','Processor','_Total','% Privileged Time'),
                    ('cpu-r','System',None,'Processor Queue Length'),
                    ('mem-free','Memory',None,'Available Mbytes'),
                    ('mem-pages-ps','Memory',None,'Pages/sec'),
                    ('disk-readtime','PhysicalDisk','_Total','% Disk Read Time'),
                    ('disk-writetime','PhysicalDisk','_Total','% Disk Write Time'),
                    ('disk-queue','PhysicalDisk','_Total','Current Disk Queue Length'),
                    ('disk-rbps','PhysicalDisk','_Total','Disk Read Bytes/sec'),
                    ('disk-wbps','PhysicalDisk','_Total','Disk Write Bytes/sec'),
                    ('disk-rps','PhysicalDisk','_Total','Disk Reads/sec'),
                    ('disk-wps','PhysicalDisk','_Total','Disk Writes/sec'),
                    ('sql-qps','SQLServer:SQL Statistics',None,'Batch Requests/sec'),
                    ('sql-tps','SQLServer:Databases','_Total','Transactions/sec'),
                    ('sql-connections','SQLServer:General Statistics',None,'User Connections'),
                    ('sql-fullscans','SQLServer:Access Methods',None,'Full Scans/sec'),
                    ('sql-targetmemory','SQLServer:Memory Manager',None,'Target Server Memory (KB)'),
                    ('sql-totalmemory','SQLServer:Memory Manager',None,'Total Server Memory (KB)'),
                    ('sql-dataspace','SQLServer:Databases','_Total','Data File(s) Size (KB)'),
                    ('sql-logspace','SQLServer:Databases','_Total','Log File(s) Size (KB)'),
                    ('sql-cachehitratio','SQLServer:Buffer Manager',None,'Buffer cache hit ratio'),
                    ('ws-bps','Web Service','_Total','Bytes Total/sec'),
                    ('ws-rps','Web Service','_Total','Total Method Requests/sec'),
                    ('ws-connections','Web Service','_Total','Current Connections')
                    #('ni-bps','Network Interface','_Total','Bytes Total/sec')                                    

                ]

        counters, instances = win32pdh.EnumObjectItems(None, None, 'Network Interface', win32pdh.PERF_DETAIL_WIZARD)
        #print instances            

        for i, n in enumerate(instances):
            paths.append( ('ni-bps' + str(i),'Network Interface',n,'Bytes Total/sec') )

        #print paths

        counters = {}

        base = win32pdh.OpenQuery()
        #print base

        for path in paths:
            counterPath = win32pdh.MakeCounterPath( (None,path[1],path[2], None, -1, path[3]) ) 
            
            if win32pdh.ValidatePath(counterPath) == 0:
                #print path
                counter = win32pdh.AddCounter(base, counterPath)
                #print counter
                counters[path[0]] = counter
            #else:
                #print path[0], '------path is not valid'

        # collect the data for the query object. We need to collect the query data
        # twice to be able to calculate the % Processor Time 
        win32pdh.CollectQueryData(base)
        set1 = self.getProcess()

        time.sleep(1)
        win32pdh.CollectQueryData(base)

        queryData = {}
        nibps = 0

        # Get the formatted value of the counter
        for key in counters.keys():
            if key.find('ni-bps') == 0:
                nibps += win32pdh.GetFormattedCounterValue(counters[key],win32pdh.PDH_FMT_LONG)[1]
            else: 
                queryData[key] = win32pdh.GetFormattedCounterValue(counters[key],win32pdh.PDH_FMT_LONG)[1]

        queryData['ni-bps'] = nibps

        win32pdh.CloseQuery(base)

        info = {}

        cpu = {}
        cpu["us"] = getQueryValue(queryData,"cpu-us")
        cpu["sy"] = getQueryValue(queryData,"cpu-sy")
        
        cpu["id"] = 100 - float(getQueryValue(queryData,"cpu-total"))
        cpu["r"] = getQueryValue(queryData,"cpu-r")

        memory = {}
        memory["free"] = getQueryValue(queryData,"mem-free")
        memory["pages-ps"] = getQueryValue(queryData,"mem-pages-ps")

        disk = {}
        disk["readtime"] = getQueryValue(queryData,"disk-readtime")
        disk["writetime"] = getQueryValue(queryData,"disk-writetime")
        disk["queue"] = getQueryValue(queryData,"disk-queue")
        disk["rbps"] = getQueryValue(queryData,"disk-rbps")
        disk["wbps"] = getQueryValue(queryData,"disk-wbps")
        disk["bps"] = disk["rbps"] + disk["wbps"]
        disk["rps"] = getQueryValue(queryData,"disk-rps")
        disk["wps"] = getQueryValue(queryData,"disk-wps")
        disk["iops"] = disk["rps"] + disk["wps"]

        
        freespace,disksize = self.getDiskSize()
        #print freespace,disksize
        if(disksize > 0):    
            disk["size"] = disksize/(1024*1024)
            disk["used"] = (disksize - freespace) / (1024*1024)
            disk["use"] = disk["used"] * 100 / disk["size"]
        
        if("sql-qps" in queryData):
            database = {}
            sqlserver = {}

            sqlserver["qps"] = getQueryValue(queryData,"sql-qps")
            sqlserver["tps"] = getQueryValue(queryData,"sql-tps")
            sqlserver["connections"] = getQueryValue(queryData,"sql-connections")
            sqlserver["fullscans"] = getQueryValue(queryData,"sql-fullscans")
            sqlserver["targetmemory"] = getQueryValue(queryData,"sql-targetmemory")
            sqlserver["totalmemory"] = getQueryValue(queryData,"sql-totalmemory")
            sqlserver["dataspace"] = getQueryValue(queryData,"sql-dataspace")
            sqlserver["logspace"] = getQueryValue(queryData,"sql-logspace")
            sqlserver["cachehitratio"] = getQueryValue(queryData,"sql-cachehitratio")
           
            database["sqlserver"] = sqlserver

            info["database"] = database


        webserver =  {}
        iis = {}

        
        if("ws-bps" in queryData):
            iis["bps"] = getQueryValue(queryData,"ws-bps")
            iis["rps"] = getQueryValue(queryData,"ws-rps")
            iis["connections"] = getQueryValue(queryData,"ws-connections")
        #iis["requestqueued"] = float(result[col+3]) #+  float(result[col+4])
    

        webserver['iis'] = iis
        info["webserver"] = webserver

        network = {}
        network["bps"] = getQueryValue(queryData,"ni-bps")

        process = []

        
        
        set2 = self.getProcess()
        

        #self.logger.debug(set1)
        #self.logger.debug(set2)
        
        totaltime = set2['total'] - set1['total']

        
        for s in set1:
            if s == 'total' :  continue
            
            if(set2.has_key(s)):
                proc = {}
                proc["pid"] = s

                if totaltime > 0:
                    proc["cpu"] = (sum(set2[s][0:2]) - sum(set1[s][0:2]) )* 100 / totaltime
                else:
                    proc["cpu"] = 0   

                proc["mem"] = set2[s][2]
                proc["mem2"] = set2[s][3]
                proc["name"] = set2[s][4]
                proc["command"] = set2[s][5]
                process.append(proc)
            
        process = sorted(process, key=lambda d: d["cpu"])
        if len(process) > 10:
            process = process[-11:]
            
        info["infoid"] = str(uuid.uuid1())
        info["machineid"] = str(uuid.getnode())
        info["timestamp"] =  time.strftime("%Y%m%d%H%M%S", time.localtime())
        info["os"] = "windows"
        info["appkey"] = self.AppKey
        info["cpu"] = cpu
        info["memory"] = memory
        info["disk"] = disk
        info["network"] = network
        info["process"] = process

        self.val["info"] = info
        #pythoncom.CoUninitialize()
        return self.val

#end dstat_wincounter



if __name__ == '__main__':
    
    import win32security, ntsecuritycon, win32con, win32api
    privs = ((win32security.LookupPrivilegeValue('',ntsecuritycon.SE_DEBUG_NAME), win32con.SE_PRIVILEGE_ENABLED),)

    hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_ALL_ACCESS)
    win32security.AdjustTokenPrivileges(hToken, False, privs)
    win32api.CloseHandle(hToken)

    #print win32api.GetCurrentProcess()
    #print ntsecuritycon.SE_DEBUG_NAME
    counter = dstat_counter()
    r = counter.extract()
    print json.dumps(r)