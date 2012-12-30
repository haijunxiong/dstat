'''
Created on 2012-12-25

@author: Administrator
'''
import wmi,subprocess,re,json

def getWebServerInfoFromIIS7():

    webserver = {}
    sites=[]

    c = wmi.WMI(namespace="WebAdministration")
    for site in c.site():

        tsite = {}
        ip = set()
        domain = set()

        tsite["index"] = site.Id
        tsite["name"] = site.Name

        
        for bind in site.bindings:
            if bind.protocol == "http" or bind.protocol == "https":
                bindinfo = bind.bindingInformation.split(":")
                if bindinfo[2] == "":
                    bindinfo[2] = "*"

                domain.add(bindinfo[2])
                ip.add(bindinfo[0] +':'+ bindinfo[1] )


        tsite["ip"] = list(ip)
        tsite["domain"] = list(domain)
        sites.append(tsite) 
            

    webserver["type"] = "iis"
    webserver["version"] = 7
    webserver["sites"] = sites
    return webserver

w = wmi.WMI()

info={}
hardware = {}

cpus = []
cpu = {}

processors = w.Win32_Processor()
for p in processors:
    cpu = {}
    cpu["name"] = p.name
    cpu["clock"] = p.maxclockspeed
    cpu["core"] = p.numberofcores
    cpu["logicalprocessor"] = p.numberoflogicalprocessors
    cpus.append(cpu)

drives = []

diskDrives = w.Win32_DiskDrive()
for d in diskDrives:
    if d.size > 0:
        drive = {}
        drive["name"] = d.name
        drive["interfacetype"] = d.interfacetype
        drive["size"] = float(d.size)/(1024*1024)
        drives.append(drive) 
        
memory = 0        
computerSystem = w.Win32_ComputerSystem()[0]
#for c in cs:
    #print c.name,c.Manufacturer,c.Model,float(c.TotalPhysicalMemory)/(1024*1024)
memory = float(computerSystem.TotalPhysicalMemory)/(1024*1024)
         
hardware["cpu"] = cpus
hardware["memory"] = memory
hardware["disk"] = drives


info["hardware"] = hardware

software = {}
os = {}

os["name"] = computerSystem.name

partitions = []

disks = w.Win32_LogicalDisk (DriveType=3)
for d in disks:
    partition = {}
    partition["caption"] = d.caption
    partition["filesystem"] = d.filesystem
    partition["size"] = float(d.size)/(1024*1024)
    partitions.append(partition)

os["partition"] = partitions



info["software"] = software

network = {}

r = subprocess.check_output(['netstat','-an','-p','TCP'],shell=True)
ports = sorted( re.findall(':(\d+).+LISTENING',r),key=lambda d: float(d))

network["port"] = ports

os["network"] =  network

softs = []

products = w.Win32_Product()
for p in sorted(products,key = lambda d : d.caption):
    softs.append(p.caption)
    
os["soft"] = softs

webserver = getWebServerInfoFromIIS7()

os["webserver"] = webserver
software["os"] = os
print json.dumps(info)


exit(0)

products = w.Win32_Product()


for p in sorted(products,key = lambda d : d.caption):
    print str(p.caption),str(p.version)
    
exit(0)

c = wmi.WMI(namespace="MicrosoftIISv2")

for web_server in c.IIsWebServerSetting():
    print web_server.Name



exit(0) 






        

    
cs = w.Win32_ComputerSystem()
for c in cs:
    print c.name,c.Manufacturer,c.Model,float(c.TotalPhysicalMemory)/(1024*1024)        
    
processors = w.Win32_Processor()
for p in processors:
    print p.processorid,p.name,p.maxclockspeed,p.numberofcores,p.numberoflogicalprocessors
    
    
os = w.Win32_OperatingSystem()[0]
print os.caption,os.version   

products = w.Win32_Product()
for p in products:
    print str(p.caption) + ',' + str(p.version)
    
    

