import sched,time,os,json,codecs
import pythoncom
import baseinfo,runninginfo_windows,log,traceback


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
    
    def removefile(self,targetdir):
        import glob

        try:
            timefile=  time.strftime("%Y%m%d", time.localtime())

            for file in glob.glob(os.path.join(targetdir,'20[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].json')):
                filename = os.path.basename(file)
                #print filename
                
                timefile=int(timefile)-3
                #print filename[0:8]
                
                removefile=int(filename[0:8])
                if (removefile<timefile):
                    os.remove(file)
        except Exception as myexce:
            #print myexce
            #raise myexce
            pass
                
    def perform(self):
        #print "perform",self.update
        try:
            pythoncom.CoInitialize()

            datadir = os.path.join(os.getcwd(),'tmatrixdata')
            if not os.path.exists(datadir):
                os.makedirs(datadir)

            self.removefile(datadir)    
            #print datadir

            baseinfofile = os.path.join(os.getcwd(),'tmatrixdata','baseinfo.json')
            if not os.path.exists(baseinfofile):
                info = baseinfo.BaseInfo()
                baseinfos = json.dumps(info.getBaseInfo())

                try:
                    f = codecs.open(baseinfofile, encoding='utf-8', mode='w')
                    f.write(baseinfos)
                finally:                
                    f.close()

            filename = time.strftime("%Y%m%d%H.json", time.localtime())
            runninginfofile = os.path.join(os.getcwd(),'tmatrixdata',filename)

            counter = runninginfo_windows.dstat_counter()
            r = counter.extract()
            runninginfos = json.dumps(r)

            try:
                f = codecs.open(runninginfofile, encoding='utf-8', mode='a')
                f.write(runninginfos)
                f.write('\r\n')
            finally:
                f.close()
            

        except Exception as myexception:
            try:
                logger = log.log()
                logger.error(myexception)

            except:
                pass

            raise myexception
                
        else:
            pass            
        finally:
            pythoncom.CoUninitialize()
            #pass
                    
if __name__ == '__main__':
    service = statservice()
    service.perform()