'''
Created on 2012-12-25

@author: mengjia
'''
import wmi,subprocess,re,json,_winreg,uuid
#import pythoncom



class BaseInfo():

    def getWebServerInfoFromIIS6(self):
        webserver = {}
        sites=[]
        siteindex = 1

        try:
            c = wmi.WMI(namespace="MicrosoftIISv2")
        except:
            return webserver

        try:

            for server in c.IIsWebServerSetting():
                site = {}
                ip = set()
                domain = set()

                site["index"] = siteindex
                siteindex += 1
                site["name"] = str(server.Name)

                for bind in server.ServerBindings:
                    if(bind.hostname == ""):
                        bind.hostname = "*"
                        
                    if(bind.ip == ""):
                        bind.ip = "*"   

                    domain.add(str(bind.hostname))
                    ip.add(str(bind.ip) +':'+ str(bind.port) )
                
                site["ip"] = list(ip)
                site["domain"] = list(domain)
                sites.append(site) 
        except:
            pass

        webserver["type"] = "iis"
        webserver["version"] = 6
        webserver["sites"] = sites

        return webserver

    def getWebServerInfoFromIIS7(self):

        webserver = {}
        sites=[]

        try:
            c = wmi.WMI(namespace="WebAdministration")
        except:
            return webserver    

        try:
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
        except:
            pass            

        webserver["type"] = "iis"
        webserver["version"] = 7
        webserver["sites"] = sites
        return webserver

    def getCpus(self):
        cpus = []

        try:
            processors = self.w.Win32_Processor()
            for p in processors:
                cpu = {}
                try:
                    cpu["name"] = p.name
                    cpu["clock"] = p.maxclockspeed
                    cpu["core"] = p.numberofcores
                    cpu["logicalprocessor"] = p.numberoflogicalprocessors
                except AttributeError:
                    pass

                cpus.append(cpu)
        except:
            pass

        return cpus

    def getInstalledSoftFromWmi(self):
        softs = set()

        try:
            products = self.w.Win32_Product()
            for p in sorted(products,key = lambda d : d.caption):
                softs.add(p.caption)
        except:
            pass        
        
        return list(softs)


    def getInstalledSoftFromRegistry(self):
        softs = set()

        try:
            r = wmi.Registry ()
            result, names = r.EnumKey (hDefKey=_winreg.HKEY_LOCAL_MACHINE, sSubKeyName=r"Software\Microsoft\Windows\CurrentVersion\Uninstall")

            keyPath = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
         
            for subkey in names:
                try:
                    path = keyPath + "\\" + subkey
                    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path, 0, _winreg.KEY_ALL_ACCESS) 
                    
                    temp = _winreg.QueryValueEx(key, 'DisplayName')
                    display = str(temp[0])
                    if display == '' or display.lower().startswith('hotfix'):
                        continue

                    softs.add(display)                
                except:
                    pass
        except:
            pass

        return list(softs)

    def getDrives(self):
        drives = []

        try:
            diskDrives = self.w.Win32_DiskDrive()
            for d in diskDrives:
                if d.size > 0:
                    drive = {}
                    drive["name"] = d.name
                    drive["interfacetype"] = d.interfacetype
                    drive["size"] = float(d.size)/(1024*1024)
                    drives.append(drive)
        except:
            pass

        return drives

    def getMemory(self):
        try:
            computerSystem = self.w.Win32_ComputerSystem()[0]
            return float(computerSystem.TotalPhysicalMemory)/(1024*1024)
        except:
            return 0

    def getPartition(self):
        partitions = []

        try:
            disks = self.w.Win32_LogicalDisk (DriveType=3)
            for d in disks:
                partition = {}
                partition["caption"] = d.caption
                partition["filesystem"] = d.filesystem
                partition["size"] = float(d.size)/(1024*1024)
                partitions.append(partition)
        except:
            pass

        return partitions    

    def getOsName(self):
        try:
            computerSystem = self.w.Win32_ComputerSystem()[0]
            return computerSystem.name
        except:
            return ''


    def getOs(self):
        os = {}

        os["name"] = self.getOsName()
        os["partition"] = self.getPartition()

        softs = self.getInstalledSoftFromWmi()

        if len(softs) <= 0:
            softs = self.getInstalledSoftFromRegistry()
        
        os["soft"] = softs

        webserver = self.getWebServerInfoFromIIS7()

        if len(webserver) <= 0:
            webserver = self.getWebServerInfoFromIIS6()

        os["webserver"] = webserver

        os["network"] =  self.getNetwork()

        return os

    def getNetwork(self):
        network = {}
        try:
            r = subprocess.check_output(['netstat','-an','-p','TCP'],shell=True)
            ports = sorted( re.findall(':(\d+).+LISTENING',r),key=lambda d: float(d))

            network["port"] = ports
        except:
            pass

        return network

    def getBaseInfo(self):

        #pythoncom.CoInitialize()

        try:
            self.w = wmi.WMI()

            info={}
            hardware = {}         
            hardware["cpu"] = self.getCpus()
            hardware["memory"] = self.getMemory()
            hardware["disk"] = self.getDrives()

            software = {}
            software["os"] = self.getOs()

            info["machineid"] = str(uuid.getnode())
            info["hardware"] = hardware
            info["software"] = software
            return info
        finally:
            #pythoncom.CoUninitialize()
            pass


if __name__ == '__main__':
    info = BaseInfo()
    print json.dumps(info.getBaseInfo())

