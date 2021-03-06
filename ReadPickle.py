#!/usr/bin/python

# ReadTH.py Read from 8266 /data
import urllib
import re
from datetime import *
import time
import math
import sys
import pickle
import os.path

os.chdir('/home/pi/Devel/tmonitor')
# Global variables
strURL40 = 'http://192.168.0.40:8484/data'
strURL41 = 'http://192.168.0.41:8484/data'
spicklename = 'ReadThr.pkl'
pickleVer = 100 # pickle version pre rain
#sFileDataName = './templates/th_data.txt'
sFileDataFormat = './templates/readTHRdata%d.txt'
sFileMinMax = './templates/ReadThrMaxMin.txt'
sHTMLname = './templates/ReadThr.html'
sFilePlot = './templates/thrplot.html'
sMDformat = '%b %d' # can add %H for each hour or %M for minutes
SMDHformat = '%b %d %H' 
sleepmin = 10
bBreak = True

fInvalid = -999.9 # invalid value (not read sensor)

# for test
sleepmin = 5
sMDformat = '%b %d %H %M'
##bBreak = True
## SMDHformat '%b %d %H %M'

strNameVer = 'ReadTHR.py 100 00'
#Program Changes
# 17-03-22 only read last few lines of sFileDataFormat and sFileMinMax files
# 17-03-23 PickelVer = 100, added rain data processing
# 17-03-24 rainBase set to rainTotal when sensor reset


#determine version
Python3 = True
(major,minor, micro, level, serial) = sys.version_info
if (major == 2):
    Python3 = False
if Python3:
    import urllib.request
    import re
else:
    import urllib
    import re

# ------------ Dew Point Formulas ------------
#Centigrate
def TdewC(TC, RH):
    try:
        Tdc = 243.04*(math.log(RH/100.0)+((17.625*TC)/(243.04+TC)))/(17.625-math.log(RH/100.0)-((17.625*TC)/(243.04+TC)))   
        return Tdc
    except:
        return 0.0

#Fahrenheit
def TdewF(TF, RH):
    Tdf = 32.0 + TdewC((TF-32.0)*5.0/9.0, RH) * 9.0/5.0
    return Tdf

# ------------ Classes ------------

# read t,h,rcount, rstring, [name]
def read_t_h_base(s_url, bAddName):
    temp = fInvalid
    humid = fInvalid
    rain = 0
    rainDate = ''
    sname = "Unknown"
    readCount = 0
    bRead = False
    # Try reading up to 5 times
    while (readCount < 5):
        try:
            if Python3:
                with urllib.request.urlopen(s_url) as response:
                    data = response.read()    
            else:
                f = urllib.urlopen(s_url)
                data = f.read()
                f.close()

            # Decode the data
            sdata = data.decode("utf-8")

            res = re.findall('temperature\[(.*?)]', sdata)
            if len(res)> 0:
                temp = float(res[0])

            res = re.findall('humidity\[(.*?)]', sdata)
            if len(res)> 0:
                humid = float(res[0])

            res = re.findall('rain\[(.*?)]', sdata)
            if len(res)> 0:
                rain = float(res[0])
                
            res = re.findall('rainDate\[(.*?)]', sdata)
            if len(res)> 0:
                rainDate = res[0]
                

            if (bAddName):
                res = re.findall('name\[(.*?)]', sdata)
                if len(res)> 0:
                    sname = res[0] 
                
            bRead = True
            break
        except:
            readCount += 1
               
        print('Could not read ' + s_url + ' try ' + str(readCount))
        time.sleep(2) # wait 5 seconds between reads
	    	
    if not bRead:             
        print('*** read error at *** ' + str(datetime.today()))

    if (bAddName):
        return (temp, humid, rain, rainDate, sname)
    return (temp, humid, rain, rainDate)

def read_t_h(s_url):
    return read_t_h_base(s_url, False)

def read_t_h_name(s_url):
    return read_t_h_base(s_url, True)

def sTimeap(dtime):
#    shms = dtime.strftime("%I:%M:%S") don't need seconds
    shms = dtime.strftime("%I:%M")
    if dtime.hour < 12:
        shms += 'a'
    else:
        shms += 'p'
    return shms   
        
class ValTime():
    def __init__(self, val, dtime):
        self.val = val
        self.dtime = dtime
    def showdate(self):
        return self.dtime.strftime("%b %d ")
    def showtime(self):
        shms = sTimeap(self.dtime)
        return shms

class MinMax99():
    def __init__(self):
        self.max = ValTime(-9e99, datetime.now())
        self.min = ValTime(9e99, datetime.now())
    
class MinMax():
    def __init__(self):
        self.max = ValTime(-9e99, datetime.now())
        self.min = ValTime(9e99, datetime.now())
        self.rainBase = 0
        self.rainTotal = 0
        self.rainDate = ''
        self.rainDayStart = 0
        self.rainHourStart = 0
    def toStr(self):
        stmax = sTimeap(self.max.dtime)
        stmin = sTimeap(self.min.dtime)
        rainDay = self.rainTotal - self.rainDayStart
        print('rainDayhStart ' + str(self.rainDayStart)) #test
        sMxtMnt = 'Tx=%.1f @ %s, Tm=%.1f @ %s' % (self.max.val,stmax,self.min.val,stmin)
        if (rainDay > 0):
            sMxtMnt = sMxtMnt + ' Rain ' + str(int(rainDay))           
        return sMxtMnt
    def UpdateRain(self, rain, rainDate):
        if (rainDate == 'NOT_SET'):
            return
#        print ('Pre base = ' + str(self.rainBase) + ' Total = ' + str(self.rainTotal))
        if (self.rainDate != rainDate):
            self.rainBase = self.rainTotal
            self.rainDate = rainDate
#            print ('Post base = ' + str(self.rainBase) + ' Total = ' + str(self.rainTotal))
        self.rainTotal = self.rainBase + rain

class CSensor():
    def __init__(self, sURL, id):
         self.temp = fInvalid
         self.humid = fInvalid
         self.dtime = datetime.now()
         self.mm = MinMax()
         self.sURL = sURL
         self.sname = ''
         self.id = id
         self.sOldDH = '' # time string from old file YYYY MMM DD HH
         
    def getDataFilename(self):
        sdatafile = sFileDataFormat % self.id
        return sdatafile



# routines for data file for each sensor

def getLastDataFileDate(fname):
    # if the file exists and contains this time, then return
    sOld = 'none'
    try:
        with open(fname,"r") as file:
            # read about last 5 lines to get last
            # assume line size 50 - 240 characters
            nToRead = 5 * 50
            file.seek(0, 2)
            flen = file.tell()
            file.seek(max(0, flen - nToRead))
            text = file.read()
        # Get the last line
        splitstr = text.splitlines()
        laststr = splitstr[len(splitstr)-1]
        ind = laststr.find('T')
        # Do not add if strTime equal
        sOld = laststr[0:ind-1]
    except:
        pass
    print ('fname', fname, 'sOld', sOld)
    return sOld

def UpdateFileOne(asensor):
    sDH = asensor.dtime.strftime(SMDHformat)
    #check if already in file
    if sDH == asensor.sOldDH:
        return 0
    nRain = asensor.mm.rainTotal - asensor.mm.rainHourStart
    sTemp = '%s T=%.1f, H=%.1f R=%f\n' % (sDH,asensor.temp, asensor.humid, nRain) 
    with open(asensor.getDataFilename(),"a") as file:
        file.write(sTemp)
        asensor.sOldDH = sDH
        # reset hour start total
        asensor.mm.rainHourStart = asensor.mm.rainTotal
    return 1


# ----------  routine to update all min and maxes
def updateOneMM(asensor):
    if asensor.temp == fInvalid:
        return False
    bChange = False
    if asensor.temp < asensor.mm.min.val:
        asensor.mm.min.val = asensor.temp
        asensor.mm.min.dtime = asensor.dtime
        bChange = True       
    if asensor.temp > asensor.mm.max.val:
        asensor.mm.max.val = asensor.temp
        asensor.mm.max.dtime = asensor.dtime
        bChange = True
    return bChange

def rewritePickle():
#    print ('***** update pickle **** V:' + str(pickleVer))
    pkl_file = open(spicklename, 'wb')
    pickle.dump(pickleVer, pkl_file) 
    for asensor in allsensors:
        pickle.dump(asensor.mm, pkl_file)
    pkl_file.close()

        
# update all and rewrite pickle if change
def updateAllMM():
    bChange = False
    global curVer
    for asensor in allsensors:
        bChange |= updateOneMM(asensor)
    if bChange or (curVer != pickleVer): #update pickle file
        rewritePickle()

    return bChange

def writeMinMaxFile(sDate):
    stext = sDate + ': '
    for asensor in allsensors:
        scur_sensor = '{%d, %s, ' % (asensor.id, asensor.sname)
        scur_sensor += asensor.mm.toStr() + '} '
        stext += scur_sensor
    stext += '\n'
    with open(sFileMinMax,"a") as file:
        file.write(stext)
    

### --------- HTML routines
sprefix = """<!DOCTYPE HTML>
<html>
<head>
<title>T RH data R</title>
</Head>
<font size='6'>{{ date }}(%s) </font>&nbsp;&nbsp;
<font size='16'> <a HREF="../thrplot">Plot</a> </font>
"""
spostfix = """
</html>
"""

stemphumid = """
<br><font size='16' color='blue'><b>%s</b>:</font>&nbsp;&nbsp;<font size='16' color='red'>%.1f&deg;</font>&nbsp;&nbsp;
<font size='16' color='green'>%.1f%% rh</font>&nbsp;&nbsp;
<font size='16' color='black'>%.1f&deg; dew pt</font><font size='14' color='black'>
"""

smmline = """
<br>
<font size='16'>Max</font>&nbsp;&nbsp;
<font size='16' color='red'>%s&deg;</font>&nbsp;&nbsp;
<font size='16' color='blue'><b>%s</b>:</font>&nbsp;&nbsp;
<font size='16'>Min</font>&nbsp;&nbsp;
<font size='16' color='red'>%s&deg;</font>
&nbsp;<font size='16' color='blue'><b>%s</b>:</font>
"""

def MMStrToHTML(sMM):
    sMM +='}'
    res = re.findall('Tx=(.*?) @ (.*?), Tm=(.*?) @ (.*?)}', sMM)
    if len(res) == 0:
        return ''
    if len(res[0]) < 4:
        return ''
    (stx, sdx, stm, sdm) = res[0]
    stext = smmline % res[0]
    return stext

def MMfromFile(id):
    nLines = 3
    s_id = str(id)
    stemp = ''
    try:
        with open(sFileMinMax,"r") as file:
            # only read about 2 * nLines (assumes 105 - 200 char/line)
            nToRead = nLines * 2 * 105
            file.seek(0, 2)
            flen = file.tell()
            file.seek(max(0, flen - nToRead))
            text = file.read()
            splitstr = text.splitlines()
            istart = len(splitstr) - nLines
            if istart < 0:
                istart = 0
            # add those that match id
            for ii in range(len(splitstr)-1,istart-1, -1):
                sline = splitstr[ii]
                res = re.findall('.*?{(.*?})', sline)
                # include MMM DD
                stemp += "<br><font size='6'>%s:</font>" % sline[0:6]
                for sMM in res:
                    if s_id == sMM[0:2]:
                        stemp += MMStrToHTML(sMM)
            return stemp
    except:
        return stemp
            
def writehtml():
    shtml =  sprefix % ('THR ' + datetime.now().strftime('%I:%M:%S %p'))
    for asensor in allsensors:
        tdewf = TdewF(asensor.temp, asensor.humid)
        temphtml = stemphumid % (asensor.sname, asensor.temp, asensor.humid, tdewf)
        # add rain if non-zero
        if (asensor.mm.rainTotal > 0):
            dayRain = asensor.mm.rainTotal - asensor.mm.rainDayStart
            sRain = "&nbsp;&nbsp;<font size='16' color='blue'>Rain %.0f</font>" % (dayRain)
            temphtml += sRain
        shtml += temphtml

    # Add max, min values
    sName = "<br><font size='6'>Max Min </font><font size='6' color='blue'>%s:&nbsp;&nbsp</font>" % allsensors[0].sname
    sDate = "<font size='6'>%s:</font>" % datetime.now().strftime('%b %d')
    sMM = allsensors[0].mm.toStr()
    shtml += sName + sDate + MMStrToHTML(sMM)

    shtml += MMfromFile(allsensors[0].id)

    shtml += spostfix
        
    with open(sHTMLname,'w') as file:
        file.write(shtml)
        
## ------------- Write thrplot.html ----------------

stplotHeader = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
	<title>Temperature Graph</title>
	<link href="static/examples.css" rel="stylesheet" type="text/css">
	<!--[if lte IE 8]><script language="javascript" type="text/javascript" src="../../excanvas.min.js"></script><![endif]-->
	<script language="javascript" type="text/javascript" src="static/flot/jquery.js"></script>
	<script language="javascript" type="text/javascript" src="static/flot/jquery.flot.js"></script>
	<script type="text/javascript">

	$(function() {

		var tval = [
"""
stplotFooter = """		];

		var plot = $.plot("#placeholder", [
			{ data: tval, label: "T"}
		], {
			series: {
				lines: {
					show: true
				},
				points: {
					show: true
				}
			},
			grid: {
				hoverable: true,
				clickable: true
			},
			//yaxis: {
			//	min: -1.2,
			//	max: 1.2
			//}
		});

		$("<div id='tooltip'></div>").css({
			position: "absolute",
			display: "none",
			border: "1px solid #fdd",
			padding: "2px",
			"background-color": "#fee",
			opacity: 0.80
		}).appendTo("body");

		$("#placeholder").bind("plothover", function (event, pos, item) {

			if ($("#enablePosition:checked").length > 0) {
				var x=(pos.x + 24)%24;
				var ampm = "a";
				if (x >= 12) {
					ampm = "p";
				}
				x = x % 12;
				var xh = Math.floor(x);
				var xm = (x - xh)*60;
				if (xh == 0)
					xh=12;
				var str = "( at " + xh.toFixed(0) +":" + xm.toFixed(0)+ ampm + ", T=" + pos.y.toFixed(2) + "*F)";
				$("#hoverdata").text(str);
			}

			if (item) {
				var x = item.datapoint[0],
					y = item.datapoint[1].toFixed(2);
				x = (x+24) % 24;
				var ampm = "a";
				if (x >= 12) {
					ampm = "p";
				}
				x = x % 12;
				if (x >= 0 && x < 1.0) {
                                           x += 12;
                                }
				x = x.toFixed(2) + ampm;
				$("#tooltip").html(item.series.label + " at " + x + " = " + y + "*F")
					.css({top: item.pageY+5, left: item.pageX+5})
					.fadeIn(200);
			}
		});

		$("#placeholder").bind("plotclick", function (event, pos, item) {
			if (item) {
				$("#clickdata").text(" - click point " + item.dataIndex + " in " + item.series.label);
				plot.highlight(item.series, item.datapoint);
			}
		});
	});

	</script>
</head>
<body>
	<div id="header">
		<h2>24 Hour Temperature Plot</h2>
	</div>

	<div id="content">

		<div class="demo-container">
			<div id="placeholder" class="demo-placeholder"></div>
		</div>

		<p>Try pointing and clicking on the points.</p>

		<p>
			<label><input id="enablePosition" type="checkbox" checked="checked"></input>Show mouse position</label>
			<span id="hoverdata"></span>
			<span id="clickdata"></span>
		</p>
	</div>
</body>
</html>
"""

def write_thplot(asensor):
       #Get last 10 lines
    sLast = ""
    stplotText = ""
    ihrOffset = 0
    sFileDataName = asensor.getDataFilename()
    if os.path.isfile(sFileDataName):
        with open(sFileDataName,"r") as file:
            # only read about 2 * 75 (assumes 50 - 100 char/line)
            nToRead = 27 * 2 * 50
            file.seek(0, 2)
            flen = file.tell()
            file.seek(max(0, flen - nToRead))
            textData = file.read()
            splitstr = textData.splitlines()
            if len(splitstr) < 27:
                print ('** Warning ** Read ') + str(len(splitstr)) + ' lines'
            # show 25 most recent
            splitstr.reverse()
            ilast = 25
            if ilast > len(splitstr):
                ilast = len(splitstr)
            for iline in range(0, ilast):
                sLast += splitstr[iline] + "<BR>\n"
                # add values for plotting
                sline = splitstr[iline]
                ieq = sline.find('=')
                iend = sline.find('H=')
                iextra = sline.find(',')
                if (iextra > ieq):
                    sline = sline[:iextra]
                if (ieq >= 0):
                    hr = int(sline[7:9])
                    tempval=float(sline[ieq+1:iend])
                    if (tempval != fInvalid):
                        stplotText = '[' + str(hr + ihrOffset) + ',' + str(tempval) + '], ' + stplotText
                    if (hr == 0):
                       ihrOffset = -24 

    splothtml = stplotHeader + stplotText + stplotFooter
    with open(sFilePlot,'w') as file:
        file.write(splothtml) 
        
################ Initialization -------------------
print (strNameVer)

allsensors = (CSensor(strURL40, 40), CSensor(strURL41, 41))

for asensor in allsensors:
    (t, h, rain, rainDate, sname) = read_t_h_name(asensor.sURL) 
    print (sname + ': T = ' + str(t) + ' H = ' + str(h) + ' R = ' + str(rain))
    asensor.sname = sname
    asensor.temp = t
    asensor.humid = h
    asensor.mm.UpdateRain(rain, rainDate)
    asensor.dtime = datetime.now()
    #get datafile date
    asensor.sOldDH = getLastDataFileDate(asensor.getDataFilename())
    
    
 # try to read in latest min-max for today

bPickleOpen = False
try:
    curVer = 0 # in case no picklename
    pkl_file = open(spicklename, 'rb')
    curVer = pickle.load(pkl_file)
    print('Cur Pickle version = ' + str(curVer))
    bPickleOpen = True
    if curVer == 99:
        for asensor in allsensors:
            mmOld = pickle.load(pkl_file)
            asensor.mm.max = mmOld.max
            asensor.mm.min = mmOld.min
    else: # 100
        for asensor in allsensors:
            asensor.mm = pickle.load(pkl_file)
except:
    print('Problem with initial: ' + spicklename)
if bPickleOpen:
    pkl_file.close()

if 0: # used to reset maximum
    allsensors[0].mm.max = ValTime(-9e99, datetime.now())
    print (allsensors[0].mm.max)
##x = 1/0

# Print out Pickle Results
print ('Pickle ver = ' + str(curVer))
sindent = '    '
for asensor in allsensors:
    print (asensor.sname)
    print ('max ' + str(asensor.mm.max.val) +  ' at ' + str(asensor.mm.max.dtime))
    print ('min ' + str(asensor.mm.min.val) +  ' at ' + str(asensor.mm.min.dtime))
    print (sindent + 'rainBase = ' + str(asensor.mm.rainBase))
    print (sindent + 'rainTotal = ' + str(asensor.mm.rainTotal))
    print (sindent + 'rainDatee = ' + str(asensor.mm.rainDate))
    print (sindent + 'rainDayStarte = ' + str(asensor.mm.rainDayStart))
    print (sindent + 'rainHourStarte = ' + str(asensor.mm.rainHourStart))

    
    


        
