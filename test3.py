import StringIO
import traceback
import wmi
import _winreg
 
r = wmi.Registry ()
result, names = r.EnumKey (hDefKey=_winreg.HKEY_LOCAL_MACHINE, sSubKeyName=r"Software\Microsoft\Windows\CurrentVersion\Uninstall")

keyPath = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
 
for subkey in names:
    try:
        path = keyPath + "\\" + subkey
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path, 0, _winreg.KEY_ALL_ACCESS) 
        try:
            temp = _winreg.QueryValueEx(key, 'DisplayName')
            display = str(temp[0])
            if display == '' or display.lower().startswith('hotfix'):
                continue

            print(display )
        except:
            pass
 
    except:
        pass
 
