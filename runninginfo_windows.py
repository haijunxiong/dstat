import re,wmi,subprocess,uuid,time,json
import win32pdh, win32pdhutil
#import pythoncom

class dstat:
    def __init__(self):
        self.val = {}

class dstat_counter(dstat):
       
    def __init__(self):
        self.name = 'perfcounter'
        self.nick = ('info',)
        self.vars = ('info',)
        self.type = 'j'
        self.width = 12
        self.scale = 0
        self.val = {}
        self.w = wmi.WMI()

    def getProcess(self):
        import win32process,win32api,win32con,os

        p = {}
        p['total'] = 0
        total = 0


        procs = win32process.EnumProcesses()
        for pid in procs:
            try:
                handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
            except:
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
                    
                except:
                    pass
            

            if handle:
                handle.Close()

        p['total'] = total
        
        return p        

        #self.open('/proc/%s/schedstat' % ownpid)
    def getProcess2(self):
        p = {}
        p['total'] = 0
        total = 0

        try:
          
            process = self.w.Win32_Process(['processid','KernelModeTime','Name','ExecutablePath','privatepagecount','usermodetime','workingsetsize'])
            for proc in process:
                p[str(proc.ProcessId)] = (float(proc.UserModeTime),float(proc.KernelModeTime),float(proc.privatepagecount)/(1024*1024),float(proc.workingsetsize)/(1024*1024),proc.Name,proc.ExecutablePath)
                total +=    float(proc.UserModeTime)  + float(proc.KernelModeTime)
                p['total'] = total
        except:
            pass

        return p
    
    def getDiskSize(self):
        freespace = 0
        disksize = 0

        try:
            fixed_disks = self.w.Win32_LogicalDisk (DriveType=3)
            for fdisk in fixed_disks:
                freespace += float(fdisk.freespace)
                disksize += float(fdisk.size)
        except:
            pass

        return (freespace,disksize)

    def extract(self):

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

        # open the query, and add the counter to the query
        #print win32pdhutil.GetPerformanceAttributes("Process(_Total)","% ProcessorTime")
        base = win32pdh.OpenQuery()
        #print base

        #elements : (machineName, objectName, instanceName, parentInstance, instanceIndex, counterName)

        for path in paths:
            counterPath = win32pdh.MakeCounterPath( (None,path[1],path[2], None, -1, path[3]) ) 
            
            if win32pdh.ValidatePath(counterPath) == 0:
                #print path
                counter = win32pdh.AddCounter(base, counterPath)
                #print counter
                counters[path[0]] = counter
            #else:
                #print path[0], '------path is not valid'

        #print counter
        # collect the data for the query object. We need to collect the query data
        # twice to be able to calculate the % Processor Time 
        win32pdh.CollectQueryData(base)
        set1 = self.getProcess()

        #time.sleep(1)
        win32pdh.CollectQueryData(base)

        queryData = {}
        nibps = 0

        # Get the formatted value of the counter
        #print "Uso de procesador al",  (win32pdh.GetFormattedCounterValue(counter,win32pdh.PDH_FMT_LONG)[1]), "%" 
        for key in counters.keys():
            if key.find('ni-bps') == 0:
                nibps += win32pdh.GetFormattedCounterValue(counters[key],win32pdh.PDH_FMT_LONG)[1]
            else: 
                queryData[key] = win32pdh.GetFormattedCounterValue(counters[key],win32pdh.PDH_FMT_LONG)[1]

        queryData['ni-bps'] = nibps

        win32pdh.CloseQuery(base)

        info = {}

        cpu = {}
        cpu["us"] = queryData["cpu-us"]
        cpu["sy"] = queryData["cpu-sy"]
        
        cpu["id"] = 100 - float(queryData["cpu-total"])
        cpu["r"] = queryData["cpu-r"]

        memory = {}
        memory["free"] = queryData["mem-free"]
        memory["pages-ps"] = queryData["mem-pages-ps"]

        disk = {}
        disk["readtime"] = queryData["disk-readtime"]
        disk["writetime"] = queryData["disk-writetime"]
        disk["queue"] = queryData["disk-queue"]
        disk["rbps"] = queryData["disk-rbps"]
        disk["wbps"] = queryData["disk-wbps"]
        disk["bps"] = disk["rbps"] + disk["wbps"]
        disk["rps"] = queryData["disk-rps"]
        disk["wps"] = queryData["disk-wps"]
        disk["iops"] = disk["rps"] + disk["wps"]

        
        freespace,disksize = self.getDiskSize()        
        
        if(disksize > 0):    
            disk["size"] = disksize/(1024*1024)
            disk["used"] = (disksize - freespace) / (1024*1024)
            disk["use"] = disk["used"] * 100 / disk["size"]
        
        if("sql-qps" in queryData):
            database = {}
            sqlserver = {}

            sqlserver["qps"] = queryData["sql-qps"]
            sqlserver["tps"] = queryData["sql-tps"]
            sqlserver["connections"] = queryData["sql-connections"]
            sqlserver["fullscans"] = queryData["sql-fullscans"]
            sqlserver["targetmemory"] = queryData["sql-targetmemory"]
            sqlserver["totalmemory"] = queryData["sql-totalmemory"]
            sqlserver["dataspace"] = queryData["sql-dataspace"]
            sqlserver["logspace"] = queryData["sql-logspace"]
            sqlserver["cachehitratio"] = queryData["sql-cachehitratio"]
           
            database["sqlserver"] = sqlserver

            info["database"] = database


        webserver =  {}
        iis = {}

        
        if("ws-bps" in queryData):
            iis["bps"] = queryData["ws-bps"]
            iis["rps"] = queryData["ws-rps"]
            iis["connections"] = queryData["ws-connections"]
        #iis["requestqueued"] = float(result[col+3]) #+  float(result[col+4])
    

        webserver['iis'] = iis
        info["webserver"] = webserver

        network = {}
        network["bps"] = queryData["ni-bps"]

        process = []

        
        
        set2 = self.getProcess()
        

        totaltime = set2['total'] - set1['total']

        for s in set1:
            if s == 'total' :  continue
            if(set2.has_key(s)):        
                proc = {}
                proc["pid"] = s
                proc["cpu"] = (sum(set2[s][0:2]) - sum(set1[s][0:2]) )* 100 / totaltime
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
        info["cpu"] = cpu
        info["memory"] = memory
        info["disk"] = disk
        info["network"] = network
        info["process"] = process

        self.val["info"] = info
        #pythoncom.CoUninitialize()
        return self.val

    def extractFromTypeperf(self):

        #pythoncom.CoInitialize()

        info = {}

        regexp = re.compile(r"\"(\d+\.\d+)\"")
        r = subprocess.check_output(['typeperf','-sc','1',
                                     '\Processor(_Total)\% Privileged Time',
                                     '\Processor(_Total)\% User Time',
                                     '\Processor(_Total)\% Processor Time',
                                     '\System\Processor Queue Length',
                                     '\Memory\Available Mbytes',
                                     '\Memory\Pages/sec',
                                     '\PhysicalDisk(_Total)\% Disk Read Time',
                                     '\PhysicalDisk(_Total)\% Disk Write Time',
                                     '\PhysicalDisk(_Total)\Current Disk Queue Length',
                                     '\PhysicalDisk(_Total)\Disk Read Bytes/sec',
                                     '\PhysicalDisk(_Total)\Disk Write Bytes/sec',
                                     '\PhysicalDisk(_Total)\Disk Reads/sec',
                                     '\PhysicalDisk(_Total)\Disk Writes/sec',                                     
                                     'SQLServer:SQL Statistics\Batch Requests/sec',
                                     'SQLServer:Databases(_Total)\Transactions/sec',
                                     'SQLServer:General Statistics\User Connections',
                                     'SQLServer:Access Methods\Full Scans/sec',
                                     'SQLServer:Memory Manager\Target Server Memory (KB)',
                                     'SQLServer:Memory Manager\Total Server Memory (KB)',                                     
                                     'SQLServer:Databases(_Total)\Data File(s) Size (KB)',
                                     'SQLServer:Databases(_Total)\Log File(s) Size (KB)',
                                     'SQLServer:Buffer Manager\Buffer cache hit ratio',
                                     'Web Service(_Total)\Bytes Total/sec',
                                     'Web Service(_Total)\Total Method Requests/sec',
                                     'Web Service(_Total)\Current Connections',
                                     #'Active Server Pages\Requests Queued',
                                     #'ASP.NET\Requests Queued',
                                     '\Network Interface(*)\Bytes Total/sec'                                     
                                     ],stdin=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        result = regexp.findall(r)    

        i=0

        cpu = {}
        cpu["us"] = float(result[i]); i += 1
        cpu["sy"] = float(result[i]); i += 1
        
        cpu["id"] = 100-float(result[i]); i += 1
        cpu["r"] = float(result[i]); i += 1

        memory = {}
        memory["free"] = float(result[i]); i += 1
        memory["pages-ps"] = float(result[i]); i += 1

        disk = {}
        disk["readtime"] = float(result[i]); i += 1
        disk["writetime"] = float(result[i]); i += 1
        disk["queue"] = float(result[i]); i += 1
        disk["rbps"] = float(result[i]); i += 1
        disk["wbps"] = float(result[i]); i += 1
        disk["bps"] = disk["rbps"] + disk["wbps"]
        disk["rps"] = float(result[i]); i += 1
        disk["wps"] = float(result[i]); i += 1
        disk["iops"] = disk["rps"] + disk["wps"]

        
        freespace,disksize = self.getDiskSize()        
        
        if(disksize > 0):    
            disk["size"] = disksize/(1024*1024)
            disk["used"] = (disksize - freespace) / (1024*1024)
            disk["use"] = disk["used"] * 100 / disk["size"]
        
        if(r.find("SQLServer") > 0):
            database = {}
            sqlserver = {}

            sqlserver["qps"] = float(result[i]); i += 1
            sqlserver["tps"] = float(result[i]); i += 1
            sqlserver["connections"] = float(result[i]); i += 1
            sqlserver["fullscans"] = float(result[i]); i += 1
            sqlserver["targetmemory"] = float(result[i]) / 1024; i += 1
            sqlserver["totalmemory"] = float(result[i]) / 1024; i += 1
            sqlserver["dataspace"] = float(result[i]) / 1024; i += 1
            sqlserver["logspace"] = float(result[i]) / 1024; i += 1
            sqlserver["cachehitratio"] = float(result[i]); i += 1
           
            database["sqlserver"] = sqlserver

            info["database"] = database


        webserver =  {}
        iis = {}

        
        if(r.find("Web Service") > 0):
            iis["bps"] = float(result[i]); i += 1
            iis["rps"] = float(result[i]); i += 1
            iis["connections"] = float(result[i]); i += 1
        #iis["requestqueued"] = float(result[col+3]) #+  float(result[col+4])
    

        webserver['iis'] = iis
        info["webserver"] = webserver

        network = {}
        bps = 0
        for item in result[i:]:
            bps += float(item)    
            i += 1

        network["bps"] = bps

        process = []

        '''
        set1 = self.getProcess()
        set2 = self.getProcess()
        

        totaltime = set2['total'] - set1['total']

        for s in set1:
            if s == 'total' :  continue
            if(set2.has_key(s)):        
                proc = {}
                proc["pid"] = s
                proc["cpu"] = (sum(set2[s][0:2]) - sum(set1[s][0:2]) )* 100 / totaltime
                proc["mem"] = set2[s][2]
                proc["mem2"] = set2[s][3]
                proc["name"] = set2[s][4]
                proc["command"] = set2[s][5]
                process.append(proc)
        
        process = sorted(process, key=lambda d: d["cpu"])
        if len(process) > 10:
            process = process[-11:]
        '''
            
        info["infoid"] = str(uuid.uuid1())
        info["machineid"] = str(uuid.getnode())
        info["timestamp"] =  time.strftime("%Y%m%d%H%M%S", time.localtime())
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
    counter = dstat_counter()
    r = counter.extract()
    print json.dumps(r)