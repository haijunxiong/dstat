import codecs
import time
import os
import logging
import logging.handlers

class log:
    def __init__(self):
        
        logfile = os.path.join(os.getcwd(),'tmatrixdata','tmatrixlog.txt')
        FORMAT = "%(asctime)-15s  %(message)s"
        
        self.my_logger = logging.getLogger('TMatrixLogger')
        self.my_logger.setLevel(logging.DEBUG)

        
        handler = logging.handlers.RotatingFileHandler(logfile,
        maxBytes=1024*1024,
        backupCount=5,
        )
        formatter = logging.Formatter(fmt=FORMAT)
        handler.setFormatter(formatter)

        self.my_logger.addHandler(handler)

    def error(self,message):
        try:
            self.my_logger.error(message)

            if message is Exception:
                self.my_logger.error( traceback.format_exc() )
        except:
            pass 

    def debug(self,message):
        try:
            self.my_logger.debug(message)

            if message is Exception:
                self.my_logger.debug( traceback.format_exc() )
        except:
            pass         

if __name__ == '__main__':
    logger = log()
    logger.debug('test')
    exce = Exception('exception!!')
    logger.error(exce)