import StringIO
import traceback
import wmi
from _winreg import (HKEY_LOCAL_MACHINE, KEY_ALL_ACCESS, 
                     OpenKey, EnumValue, QueryValueEx)
 
 
r = wmi.Registry ()
result, names = r.EnumKey (hDefKey=HKEY_LOCAL_MACHINE, sSubKeyName=r"Software\Microsoft\Windows\CurrentVersion\Uninstall")

keyPath = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
 
for subkey in names:
    try:
        path = keyPath + "\\" + subkey
        key = OpenKey(HKEY_LOCAL_MACHINE, path, 0, KEY_ALL_ACCESS) 
        try:
            temp = QueryValueEx(key, 'DisplayName')
            display = str(temp[0])
            if display == '' or display.lower().startswith('hotfix'):
                continue

            print(display )
        except:
            pass
 
    except:
        pass
 
