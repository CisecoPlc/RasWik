#!/usr/bin/env python

import urllib2


versionFile = 'http://files.ciseco.co.uk/Sandy/version.txt'
updateFile = 'http://files.ciseco.co.uk/Sandy/sandy_'

try:
	request = urllib2.urlopen('http://files.ciseco.co.uk/Sandy/version.txt')
	response = request.read()

except urllib2.HTTPError, e:
	print 'Unable to get latest version info - HTTPError = ' + str(e.reason)
	sys.exit(2)

except urllib2.URLError, e:
	print 'Unable to get latest version info - URLError = ' + str(e.reason)
	sys.exit(2)

except httplib.HTTPException, e:
	print 'Unable to get latest version info - HTTPException'
	sys.exit(2)

except Exception, e:
	import traceback
	print 'Unable to get latest version info - Exception = ' + traceback.format_exc()
	sys.exit(2)

print response