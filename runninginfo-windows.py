import re,wmi,subprocess,uuid,time,json

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

        #self.open('/proc/%s/schedstat' % ownpid)
    def getProcess(self):
        p = {}
        p['total'] = 0
        total = 0

        try:
            w = wmi.WMI()
            process = w.Win32_Process(['processid','KernelModeTime','Name','ExecutablePath','privatepagecount','usermodetime','workingsetsize'])
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
            fixed_disks = wmi.WMI().Win32_LogicalDisk (DriveType=3)
            for fdisk in fixed_disks:
                freespace += float(fdisk.freespace)
                disksize += float(fdisk.size)
        except:
            pass

        return (freespace,disksize)


    def extract(self):
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
                                     ],shell=True)
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

        info["infoid"] = str(uuid.uuid1())
        info["machineid"] = str(uuid.getnode())
        info["timestamp"] =  time.strftime("%Y%m%d%H%M%S", time.localtime())
        info["cpu"] = cpu
        info["memory"] = memory
        info["disk"] = disk
        info["network"] = network
        info["process"] = process

        self.val["info"] = info
#end dstat_wincounter



if __name__ == '__main__':
    counter = dstat_counter()
    counter.extract()
    print json.dumps(counter.val)