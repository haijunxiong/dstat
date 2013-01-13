import glob
import logging
import logging.handlers

LOG_FILENAME = 'tmatrixlog.txt'
# Set up a specific logger with our desired output level
my_logger = logging.getLogger('TMatrixLogger')
my_logger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
maxBytes=20,
backupCount=5,
)
my_logger.addHandler(handler)
# Log some messages
for i in range(20):
	my_logger.debug('i = %d' % i)