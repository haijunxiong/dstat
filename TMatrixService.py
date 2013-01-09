# Usage:
# service.exe install
# service.exe start
# service.exe stop
# service.exe remove

# you can see output of this program running python

import win32service
import win32serviceutil
import win32event
import win32evtlogutil
#import win32traceutil
import servicemanager
import winerror
import time
import sys
import os
import statservice
import log

class TMatrixService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TMatrixService"
    _svc_display_name_ = "TMatrixService"
    _svc_deps_ = ["EventLog"]
    #_exe_name_ = "service.exe"
    #_exe_args_ = "start"


    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop=win32event.CreateEvent(None, 0, 0, None)
        self.isAlive=True
        self.statservice = statservice.statservice() 
        #self.logger = log.log()
        #self.logger.log('init')


    def SvcStop(self):

        # tell Service Manager we are trying to stop (required)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # write a message in the SM (optional)
        import servicemanager
        #servicemanager.LogInfoMsg("aservice - Recieved stop signal")

        # set the event to call
        win32event.SetEvent(self.hWaitStop)

        self.isAlive=False

    def SvcDoRun(self):
        import servicemanager
        # Write a 'started' event to the event log... (not required)
        #
        win32evtlogutil.ReportEvent(self._svc_name_,servicemanager.PYS_SERVICE_STARTED,0,servicemanager.EVENTLOG_INFORMATION_TYPE,(self._svc_name_, ''))

        #servicemanager.LogInfoMsg("aservice - Recieved run signal,isAlive: " + str(self.isAlive))
        #self.logger.log("aservice - Recieved run signal,isAlive: " + str(self.isAlive))

        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

        # methode 1: wait for beeing stopped ...
        # win32event.WaitForSingleObject(self.hWaitStop,win32event.INFINITE)

        # methode 2: wait for beeing stopped ...
        self.timeout=1000  # In milliseconds (update every second)
        count = 0

        while self.isAlive:

            self.ReportServiceStatus(win32service.SERVICE_RUNNING)


            # wait for service stop signal, if timeout, loop again
            rc=win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            
            
            count += 1

            if count == 60 * 5:
                self.statservice.perform()
                count = 0
            

        # and write a 'stopped' event to the event log (not required)
        #
        win32evtlogutil.ReportEvent(self._svc_name_,servicemanager.PYS_SERVICE_STOPPED,0,servicemanager.EVENTLOG_INFORMATION_TYPE,(self._svc_name_, ''))

        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

        return


if __name__ == '__main__':

    import servicemanager

    #logger2 = log.log()
    #logger2.log(str(__name__))
    #logger2.log("sys.argv: " + str(sys.argv))     
    


    # if called without argvs, let's run !
    #print sys.argv
    #print os.path.abspath(servicemanager.__file__)

    #servicemanager.LogInfoMsg("sys.argv: " + str(sys.argv))
    #logger2.log("sys.argv2: " + str(sys.argv))
    
    #if len(sys.argv) == 1:
    #    sys.argv.append('start')

    
    if len(sys.argv) == 1:
        
        try:
            evtsrc_dll = os.path.abspath(servicemanager.__file__)
            servicemanager.PrepareToHostSingle(TMatrixService)
            servicemanager.Initialize('TMatrixService', None)
            servicemanager.StartServiceCtrlDispatcher()
        except win32service.error, details:
            #print unicode(details).encode('gb2312')

            if details[0] == winerror.ERROR_FAILED_SERVICE_CONTROLLER_CONNECT:
                win32serviceutil.usage()
        

        #win32serviceutil.HandleCommandLine(TMatrixService,argv=['start'])        
    else:
        win32serviceutil.HandleCommandLine(TMatrixService)
        