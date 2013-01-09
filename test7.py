import _winreg as winreg 

import win32com.client 

HKLM = winreg.HKEY_LOCAL_MACHINE 
NICs = "SYSTEM\\CurrentControlSet\\Control\\Class\\{4D36E972-E325-11CE-BFC1-08002bE10318}" 

registry = win32com.client.GetObject("winmgmts:/root/default:StdRegProv") 
EnumKey = registry.Methods_("EnumKey") 
params = EnumKey.InParameters.SpawnInstance_() 
#params.Properties_.Item("hDefKey").Value = HKLM 
params.Properties_.Item("sSubKeyName").Value = NICs 

OutParameters = registry.ExecMethod_("EnumKey", params) 
print OutParameters.Properties_.Item("ReturnValue") 
print OutParameters.Properties_.Item("sNames") 