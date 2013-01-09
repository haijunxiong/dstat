import codecs
import time

class log:
	def log(self,message):
		try:
			f = codecs.open('c:\\log.txt', encoding='utf-8', mode='a')
			f.write(time.strftime("%Y%m%d%H%M%S", time.localtime()))
			f.write('::::')
			f.write(message)
			f.write('\r\n')
		finally:    
			f.close()

if __name__ == '__main__':
	logger = log()
	logger.log('test')