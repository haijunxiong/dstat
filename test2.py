
import wmi,re
from _winreg import (HKEY_LOCAL_MACHINE, KEY_ALL_ACCESS,OpenKey, EnumValue, QueryValueEx)
 
def getInstalledSoftwareFromReg():
    softs = set()

    r = wmi.Registry ()
    
    keyPath = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    result, names = r.EnumKey (hDefKey=HKEY_LOCAL_MACHINE, sSubKeyName=keyPath)   
    return 
    reg = re.compile('^hotfix|kb(\d+)|service pack',re.I)
    for subkey in names:
        try:
            path = keyPath + "\\" + subkey
            key = OpenKey(HKEY_LOCAL_MACHINE, path, 0, KEY_ALL_ACCESS) 
            try:
                temp = QueryValueEx(key, 'DisplayName')
                display = str(temp[0])
                if display == None or display == '' or reg.search(display) <> None:
                    continue

                softs.add(display)
            except:
                pass
     
        except:
            pass
    return sorted(list(softs))
 
for item in getInstalledSoftwareFromReg():
    print item