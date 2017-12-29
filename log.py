import time

# (C) 2017 by folkert@vanheusden.com
# released under AGPL v3.0

def l(msg):
	logfile = 'feeks.dat'

	fh = open(logfile, 'a')
	fh.write('%s %s\n' % (time.asctime(), msg))
	fh.close()
