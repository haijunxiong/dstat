import sched,time,sys,linecache

def main():

	global inittime
	global update, missed

	scheduler = sched.scheduler(time.time, time.sleep)
	inittime = time.time()

	update = 0
	interval = 60

	while True:
		scheduler.enterabs(inittime + update, 1, perform, (update,))
		scheduler.run()
 
		update = update + interval
		
		
    
def perform(update):
	print "perform",update

if __name__ == '__main__':
	main()