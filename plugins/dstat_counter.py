### Author: Dag Wieers <dag$wieers,com>



class dstat_plugin(dstat):
    """
    Provide more information related to the dstat process.

    The dstat cputime is the total cputime dstat requires per second. On a
    system with one cpu and one core, the total cputime is 1000ms. On a system
    with 2 cores the total is 2000ms. It may help to vizualise the performance
    of Dstat and its selection of plugins.
    """
    def __init__(self):
        self.name = 'perfcounter'
        self.nick = ('info',)
        self.vars = ('info',)
        self.type = 'j'
        self.width = 12
        self.scale = 0
        #self.open('/proc/%s/schedstat' % ownpid)

    def extract(self):
        
        regexp = re.compile(r"\"(\d+\.\d+)\"")
        r = subprocess.check_output(['typeperf','-sc','1',
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
                                     'SQLServer:Memory Manager\Target Server Memory (KB)',
                                     'SQLServer:Memory Manager\Total Server Memory (KB)',                                     
                                     'SQLServer:Databases(_Total)\Data File(s) Size (KB)',
                                     'SQLServer:Databases(_Total)\Log File(s) Size (KB)',
                                     'SQLServer:Buffer Manager\Buffer cache hit ratio',
                                     '\Network Interface(*)\Bytes Total/sec'                                     
                                     ],shell=True)
        #print(r)
        result = regexp.findall(r)    
        #print(result)

        info = {}

        cpu = {}
        cpu["total"] = float(result[0])
        cpu["queue"] = float(result[1])

        memory = {}
        memory["free"] = float(result[2])
        memory["pages-ps"] = float(result[3])

        disk = {}
        disk["diskreadtime"] = float(result[4])
        disk["diskwritetime"] = float(result[5])
        disk["diskqueue"] = float(result[6])
        disk["diskreadbytes"] = float(result[7])
        disk["diskwritebytes"] = float(result[8])
        disk["diskreads"] = float(result[9])
        disk["diskwrites"] = float(result[10])

        col = 11

        if(r.find("SQLServer") > 0):
            database = {}
            sqlserver = {}

            sqlserver["batchrequests"] = float(result[11])
            sqlserver["transactions"] = float(result[12])
            sqlserver["connections"] = float(result[13])
            sqlserver["TargetMemory"] = float(result[14])
            sqlserver["TotalMemory"] = float(result[15])
            sqlserver["Data Space"] = float(result[16])
            sqlserver["Log Space"] = float(result[17])
            sqlserver["cachehitratio"] = float(result[18])

            col = 19

            database["sqlserver"] = sqlserver

            info["database"] = database


        network = {}
        bps = 0
        for item in result[col:]:
            bps += float(item)    

        network["bps"] = bps

        info["cpu"] = cpu
        info["memory"] = memory
        info["disk"] = disk
        info["network"] = network

        self.val["info"] = info

        #print(self.val)
        
# vim:ts=4:sw=4:et
