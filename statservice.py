import sched,time,os,json,codecs
import pythoncom
import baseinfo,runninginfo_windows


class statservice():
    def __init__(self):
        self.inittime = time.time()
        self.update = 0
        self.interval = 60

    def main(self):

        scheduler = sched.scheduler(time.time, time.sleep)
        self.inittime = time.time()

        while True:
            scheduler.enterabs(self.inittime + self.update, 1, self.perform, ())
            scheduler.run()
     
            self.update += self.interval                        
        
    def perform(self):
        #print "perform",self.update
        try:
            pythoncom.CoInitialize()

            datadir = os.path.join(os.getcwd(),'tstatdata')
            if not os.path.exists(datadir):
                os.makedirs(datadir)

            #print datadir

            baseinfofile = os.path.join(os.getcwd(),'tstatdata','baseinfo.json')
            if not os.path.exists(baseinfofile):
                info = baseinfo.BaseInfo()
                baseinfos = json.dumps(info.getBaseInfo())

                try:
                    f = codecs.open(baseinfofile, encoding='utf-8', mode='w')
                    f.write(baseinfos)
                finally:                
                    f.close()

            filename = time.strftime("%Y%m%d%H.json", time.localtime())
            runninginfofile = os.path.join(os.getcwd(),'tstatdata',filename)

            counter = runninginfo_windows.dstat_counter()
            r = counter.extract()
            runninginfos = json.dumps(r)

            try:
                f = codecs.open(runninginfofile, encoding='utf-8', mode='a')
                f.write(runninginfos)
                f.write('\r\n')
            finally:
                f.close()
        finally:
            pythoncom.CoUninitialize()
                    
if __name__ == '__main__':
    service = statservice()
    service.perform()