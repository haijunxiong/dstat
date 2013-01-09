import _winreg as winreg 
import wmi 

HKLM = 2147483650 #winreg.HKEY_LOCAL_MACHINE 
UNINSTALLERS = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall" 

registry = wmi.WMI(namespace="default").StdRegProv 
_, names = registry.EnumKey(hDefKey=HKLM,sSubKeyName=UNINSTALLERS) 
for name in names: 
	print name 
	uninstaller = UNINSTALLERS + "\\" + name 

_, value_names, value_types = registry.EnumValues(HKLM, uninstaller) 

for value_name, value_type in zip(value_names, value_types): 
	if value_type == winreg.REG_SZ: 
		_, value = registry.GetStringValue(HKLM,uninstaller, value_name) 
else: 
	value = "(Non-string value)" 

print u" ", value_name, u"=>", value 