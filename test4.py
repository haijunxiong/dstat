
import wmi,subprocess,re

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

w = getWebServerInfoFromIIS7()
print(w)