
import wmi,subprocess,re

c = wmi.WMI(namespace="MicrosoftIISv2")

webserver = {}
sites=[]
siteindex = 1


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

webserver["type"] = "iis"
webserver["version"] = 6
webserver["sites"] = sites
print(webserver)

exit(0) 


w = wmi.WMI()
products = w.Win32_Product()
for p in products:
    print str(p.caption) + ',' + str(p.version)



import _winreg
key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
count = _winreg.QueryInfoKey(key)[0]
for i in range(0,count):
    
    asubkey_name= _winreg.EnumKey(key,i)
    asubkey=_winreg.OpenKey(key,asubkey_name)
    val=_winreg.QueryValueEx(asubkey, "DisplayName")
    print val