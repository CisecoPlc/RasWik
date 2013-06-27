import zipfile
import urllib2
import os

# check for extraction directories existence
if not os.path.isdir('downloaded'):
    os.makedirs('downloaded')

if not os.path.isdir('extracted'):
    os.makedirs('extracted')


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


# path of zip files
zipFileURL = "{}{}.zip".format(updateFile, response)
outputFilename = "downloaded/Sandy_{}.zip".format(response)

response = urllib2.urlopen(zipFileURL)

zippedData = response.read()

# save data to disk
print "Saving to ",outputFilename
output = open(outputFilename,'wb')
output.write(zippedData)
output.close()

# extract the data
zfobj = zipfile.ZipFile(outputFilename)

for name in zfobj.namelist():
    (dirname, filename) = os.path.split(name)
    print "Decompressing " + filename + " on " + dirname
    if filename == '':
        if not os.path.exists("extracted/" + dirname):
            os.mkdir("extracted/" + dirname)
    else:
        fd = open("extracted/" + name,"w")
        fd.write(zfobj.read(name))
        fd.close()