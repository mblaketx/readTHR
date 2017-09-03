from serial import *
from Tkinter import *
from datetime import *
import os.path
import time

tm_version = '12'

timedeltamin = timedelta(minutes=15) #Motion interval 15

sFileName = './templates/info.html'
#sFileDataName = '/home/pi/Devel/tmonitor/templates/info_data.txt'
sMovementName = './templates/movement.txt'
sFileDataName = './templates/info_data.txt'
sFile_tplot = './templates/tplot.html'

bPrintEachTemperature = False

iOldHour = -1

class Tdate:
    def __init__(self, tini):
        self.tval = tini
        self.date = datetime.now()
        
def fattime(st):
    iat = st.find('@')
    if iat < 0:
        return (0, '')
    fval = float(st[0:iat])
    if st[-1] == '\n':
        return (fval, st[iat+1:-1])       
    return (fval, st[iat+1:])
        
serialPort = "/dev/ttyACM0"
baudRate = 9600
ser = Serial(serialPort , baudRate, timeout=0, writeTimeout=0) #ensure non-blocking

timeMin = ""
timeMax = ""
tmin = 1000
tmax = -1000
tdhmin = Tdate(1000.0)
tdhmax = Tdate(-1000.0)
lastMinMaxDay = -1
    
#get old information

def getOldMinMax():
    global lastMinMaxDay
    tmin = 1000
    tmax = -1000
    sLastDate = ""
    tmp_day_min_max = []
    try:
        with open(sFileDataName,"r") as file:

            while True:
                rline = file.readline()
                if len(rline) == 0:
                    break
                sCurDate = rline[0:6]
                if (sCurDate != sLastDate):
                    #if any data, write data for day
                    sOldDate = sLastDate
                    sLastDate = sCurDate
                    if tmin == 1000:
                        # skip if no data
                        continue
                    tmp_day_min_max.append( (sOldDate, tmin, timeMin, tmax, timeMax) )
                    tmin = 1000
                    tmax = -1000
                    timeMin = ""
                    timeMax = ""
                #process current hour
                ieq = rline.find('=')
                if ieq < 0:
                    continue
                icx = rline.find(', x=')
                if (icx < 0):
                    tval = float(rline[ieq+1:])
                    if tval < tmin:
                        tmin = tval
                        timeMin = rline[0:ieq-2]
                    if tval > tmax:
                        tmax = tval
                        timeMax = rline[0:ieq-2]
                else:
                    # new method
                    icm = rline.find(', m=')
                    if (icm == -1):
                        print 'incomplete line'
                        continue
                    else:
                        t1,s1 = fattime(rline[icx+4:icm])
                        t2,s2 = fattime(rline[icm+4:])
                        if (t1 > tmax):
                            tmax = t1
                            timeMax = rline[0:ieq-4] + s1
                            # print tmax, timeMax, 'hello'
                        if (t2 < tmin):
                            tmin = t2
                            timeMin = rline[0:ieq-4] + s2
                            # print tmin, timeMin, 'hello min'
                        
    except:
        print ('No Previous data')

    # keep last few
    iend = len(tmp_day_min_max)
    istart = max(iend-5, 0)
    day_min_max = tmp_day_min_max[istart:iend]
    tmp_day_min_max = None # don't keep
    lastMinMaxDay = datetime.today().day
    return (tmin, tmax, day_min_max, timeMin, timeMax)

# actually get old values
tmin, tmax, day_min_max, timeMin, timeMax = getOldMinMax()
#assert 0

# utility Routines
def slocAmpm(loctime):
    shms = time.strftime("%I:%M", loctime)
    if loctime.tm_hour < 12:
        shms += 'a'
    else:
        shms += 'p'
    return shms

def dostop():
    global istop
    istop = 1-istop
    if istop:
        app.butstop.configure(text='Start')
        #app.tlabel0.configure(text = 'stopped')
        app.tVar.set('vStopped')
    else:
        app.butstop.configure(text='Stop')
        #app.tlabel0.configure(text = 'started')
        app.tVar.set('vStarted')
        
 # does not work    tlabel0.text.set('new text')
    return

class App:
    def __init__(self, mroot):
        frame = Frame(mroot)
        frame.pack()

        # Top label
        self.tTime = StringVar()
        self.tlabel0 = Label(frame, width=15, justify=LEFT, textvariable=self.tTime)
        tlabel1 = Label(frame,text='Hourly Temperature')
        tlabel2 = Label(frame,text='Movement')

        self.tVar = StringVar()
        tlabel = Label(frame, justify=LEFT, textvariable=self.tVar)
        
        self.tVarMax = StringVar()
#        tmxlabel = Message(frame, width=15, textvariable=self.tVarMax)
        tmxlabel = Label(frame, justify=LEFT, textvariable=self.tVarMax)
        self.tVarMin = StringVar()
        tmnlabel = Label(frame, justify=LEFT,  textvariable=self.tVarMin)
        self.butstop = Button(frame,text='Stop',command=dostop)

        # make a text box to put the serial output
        logframe = Frame(frame)
        self.log = Text ( logframe, width=52, height=10, takefocus=0)
        ##log = Text ( frame, width=30, height=10, takefocus=0)
        self.log.pack(side=LEFT)

        #Text for last move time
        self.tLastMove = StringVar()
        labelLastMove = Label(frame, width=20, justify=LEFT, textvariable=self.tLastMove)

        #Text for last move time
        self.tLastTimeSet= StringVar()
        labelLastTimeSet= Label(frame, width=20, justify=LEFT, textvariable=self.tLastTimeSet)


        # make a scrollbar
        scrollbar_log = Scrollbar(logframe) 
        scrollbar_log.pack(side=RIGHT, fill=Y)


        # Movement Box
        moveframe = Frame(frame)
        self.move = Text ( moveframe, width=30, height=9, takefocus=0)
        self.move.pack(side=LEFT)

        # make a scrollbar
        scrollbar_move = Scrollbar(moveframe)
        scrollbar_move.pack(side=RIGHT, fill=Y)

        # geometry
        self.tlabel0.grid(row=0, column=0, sticky=W, padx=5)
        tlabel.grid(row=1, column=0, sticky=W, padx=5)
        tmxlabel.grid(row=2, column=0, sticky=W, padx=5)
        tmnlabel.grid(row=3, column=0, sticky=W, padx=5)
        self.butstop.grid(row=4, column=0, padx=10)
        labelLastTimeSet.grid(row=5, column=0, sticky=W, padx=5)
          
        tlabel1.grid(row=0, column=1, padx=10)
        logframe.grid(row=1, column=1, rowspan=4)
       
        tlabel2.grid(row=0, column=2, padx=10)
        moveframe.grid(row=1, column=2, rowspan=3)
        labelLastMove.grid(row=4, column=2, sticky=W, padx=5)

        # attach text box to scrollbar
        self.log.config(yscrollcommand=scrollbar_log.set)
        scrollbar_log.config(command=self.log.yview)

        self.move.config(yscrollcommand=scrollbar_move.set)
        scrollbar_move.config(command=self.move.yview)

    def add_log(self, text):
        self.log.insert(END, text)
        self.log.see(END)
        
    def add_movement(self, text):
        self.move.insert(END, text)
        self.move.see(END)       

def fakeread():
    global iread
    if istop == 0:
        iread += 1
        text = 'read ' + str(iread)
        processSerial(text)
    root.after(1000, fakeread) # check serial again soon

    

def readSerial():
    if istop:
       root.after(10, readSerial) # check serial again soon
       return
   
    while True:
        c = ser.read() # attempt to read a character from Serial
        
        #was anything read?
        if len(c) == 0:
            break
        
        # get the buffer from outside of this function
        global serBuffer
        
        # check if character is a delimeter
        if c == '\r':
            c = '' # don't want returns. chuck it
            
        if c == '\n':
            # do not add new line to buffer
            # serBuffer += "\n" # add the newline to the buffer
            
            #add the line to the TOP of the log
            #log.insert('0.0', serBuffer)
            processSerial(serBuffer)
            serBuffer = "" # empty the buffer
        else:
            serBuffer += c # add to the buffer
    
    root.after(10, readSerial) # check serial again soon



#make our own buffer
#useful for parsing commands
#Serial.readline seems unreliable at times too
serBuffer = ""
iread = 0
istop = 0
lastRead = "Hi"
iPrint = 0



#make a TkInter Window
root = Tk()
root.wm_title("Reading Temperature v" + tm_version)
app = App(root)

def sAmpm(sdate):
    shms = sdate.strftime("%I:%M")
    if sdate.hour < 12:
        shms += 'a'
    else:
        shms += 'p'
    return shms

def sHMSAmpm(sdate):
    shms = sdate.strftime("%I:%M:%S")
    if sdate.hour < 12:
        shms += 'a'
    else:
        shms += 'p'
    return shms

#variables for motion
iLastMotion = 0
sMotionTime = "" #full string of all motion
dateLastOn = datetime.now()
dateLastOrig = dateLastOn
sFirstOn = ""
dateFirstOn = datetime.now()
sLastSet = "" # last motion time

#other variables

#use minmax from file
#tmax = -1000
#tmin = 1000
smax = timeMax
smin = timeMin
app.tVarMin.set("Tmin= " + str(tmin) +'\n' + smin)
app.tVarMax.set("Tmax= " + str(tmax) +'\n' + smax)
        
sfind = "Temp: "
sheader = """<!DOCTYPE html>
  <head>
    <title> Info </title>
  </head>

  <body>
    <h1>Office:</h1>
    <h2>{{ date }}</h2>
    <h2> <a HREF="../tplot">Plot</a> </h2>
    <h1>
"""
sfooter = """</h1>
</body>
</html>
"""

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

# main processing routines
def AddTimeTemp(strTime, temp):
    global tdhmin, tdhmax
    global lastMinMaxDay
    global tmin,tmax
    global day_min_max
    # if the file exists and contains this time, then return
    try:
        with open(sFileDataName,"r") as file:
            text = file.read()
        # Get the last line
        splitstr = text.splitlines()
        laststr = splitstr[len(splitstr)-1]
        ind = laststr.find('T')
        # Do not add if strTime equal
        sOld = laststr[0:ind-1]
        # print '*', sOld, '*', strTime, '*'
        if strTime == sOld:
            return 0
    except:
        print 'No file'
    #if not set yet, use current temp
    if abs(tdhmax.tval) > 500:
        tdhmax.tval = temp
    if abs(tdhmin.tval) > 500:
        tdhmin.tval = temp       
    sTemp = strTime + " T=" + str(temp) \
        + ', x=' + str(tdhmax.tval)+ ' @' + tdhmax.date.strftime('%H:%M') \
        + ', m=' + str(tdhmin.tval)+ ' @' + tdhmin.date.strftime('%H:%M') + '\n'
    #reset hourly values
    tdhmax.tval = temp
    tdhmax.date = datetime.now()
    tdhmin.tval = temp
    tdhmin.date = datetime.now()   
    
    with open(sFileDataName,"a") as file:
        file.write(sTemp)
    # add to list
    app.add_log(sTemp) # no /n needed
    
    # print lastMinMaxDay, datetime.today().day, ' lastMMday, day'
    if (lastMinMaxDay != datetime.today().day):
        print 'day reset'
        tmin = temp
        tmax = temp
        shms = datetime.now().strftime('d ') + sAmpm(datetime.now())
        smin= shms
        smax = shms
        
        # each day, update minmax
        tminjunk, tmaxjunk, day_min_max, junkMin, junkMax = getOldMinMax()
    return 1

def processSerial(sserial):
    global timedeltamin
    global iLastMotion
    global sMotionTime
    global dateLastOn
    global dateLastOrig
    global sFirstOn
    global dateFirstOn
    global tmin
    global tmax
    global sfind
    global smax
    global smin
    global iOldHour
    global ser
    global sLastSet
    global iPrint
    global day_min_max
    global tdhmin, tdhmax
    
    istart = sserial.find(sfind)
    if istart == -1:
        return
    istart += len(sfind)
    iend = sserial.find("*F")
    if (iend == -1):
        return
    iMotion = int(sserial[0:1])
    tval = float(sserial[istart:iend])
    today = datetime.today()
 #   shms = today.strftime("%H:%M:%S")
 #   shms = today.strftime("%H:%M")
 #   shms = today.strftime("%I:%M %p")
##    shms = today.strftime("%I:%M")
##    if today.hour < 12:
##        shms += 'a'
##    else:
##        shms += 'p'
    shms = sAmpm(today)
    sday = today.strftime("%b %d ")
    sdayhms = sday + sHMSAmpm(today)
    app.tTime.set(sdayhms)
    app.tVar.set("T=" + str(tval))
    text = shms +  " T= " + str(tval)+ "<BR>\n"
 #   print shms, tval
    if (tval < tmin):
        tmin = tval
        smin = shms
        app.tVarMin.set("Tmin= " + str(tmin) +'\n' + smin)
    if (tval > tmax):
        tmax = tval
        smax = shms
        app.tVarMax.set("Tmax= " + str(tmax) +'\n' + smax)
    text += smax + " Tmax= " + str(tmax) + "<BR>\n"
    text += smin + " Tmin= " + str(tmin) + "<BR>\n"
    if (tval < tdhmin.tval):
        tdhmin.tval = tval
        tdhmin.date = today
    if (tval > tdhmax.tval):
        tdhmax.tval = tval
        tdhmax.date = today
    #print 'hour MinMax,date',tdhmin.tval, tdhmax.tval
    
    #old values
    for icur in day_min_max:
        (sOldDate, tmin0, timeMin0, tmax0, timeMax0) =  icur
        spartial = 'Tmin = ' + str( tmin0) + ' at ' + str(timeMin0) + \
                   '  Tmax = ' + str(tmax0) + ' at ' + str(timeMax0) + '<BR>\n'
        text += spartial

    bDoRecord = False;
    if len(sFirstOn) > 0:
        if (today > dateLastOn + timedeltamin) \
        and (today > dateLastOn + timedeltamin):
            bDoRecord = True;
    if (iMotion != iLastMotion) :
        if iMotion :
           dateLastOn = today
           if len(sFirstOn) == 0:
                sFirstOn = sHMSAmpm(today)
                dateFirstOn = today
                app.tLastMove.set("Motion:" + sFirstOn + dateFirstOn.strftime("  %b %d"))
           else:
                strMotion = dateFirstOn.strftime("%b %d ") + sFirstOn + "\nLast: " + sHMSAmpm(dateLastOn)
                app.tLastMove.set("Motion:" + strMotion)

        
    iLastMotion = iMotion   
        
    if 1:
        text += "</h1><h2>In " + sFirstOn + "  Out " + sHMSAmpm(dateLastOn) + "</h2><h1>\n"
    else:
        if (iMotion):
            text += "Motion  " + sHMSAmpm(today) + "<BR>\n"
        else:
            text += "Last Motion " + sHMSAmpm(dateLastOn) + "<BR>\n"

    if bDoRecord and len(sFirstOn) > 0 :
        #add most recent to front
        sMotionCur = dateFirstOn.strftime("%b %d ") + "In " + sAmpm(dateFirstOn) + "  Out " + sAmpm(dateLastOn)
        sMotionTime =  sMotionTime + sMotionCur + "<BR>\n" 
        sFirstOn = ""
        # write into file
        sTemp = sMotionCur + '\n'
        app.add_movement(sTemp)
        with open(sMovementName,"a") as file:
            file.write(sTemp)
        

# add data from file
    if today.hour != iOldHour:
        strNow = today.strftime('%b %d %H')
        if AddTimeTemp(strNow, tval):
            iOldHour = today.hour
            
    #Get last 10 lines
    sLast = ""
    stplotText = ""
    ihrOffset = 0
    if os.path.isfile(sFileDataName):
        with open(sFileDataName,"r") as file:
            textData = file.read()
            splitstr = textData.splitlines()
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
                iextra = sline.find(',')
                if (iextra > ieq):
                    sline = sline[:iextra]
                if (ieq >= 0):
                    hr = int(sline[7:9])
                    tempval=float(sline[ieq+1:])
                    stplotText = '[' + str(hr + ihrOffset) + ',' + str(tempval) + '], ' + stplotText
                    if (hr == 0):
                       ihrOffset = -24 
                    
        text += sLast

    text += "</h1><h2>" + sMotionTime + "</h2><h1>"

    shtml = sheader + text + sfooter
    with open(sFileName,'w') as file:
        file.write(shtml)

    splothtml = stplotHeader + stplotText + stplotFooter
    with open(sFile_tplot,'w') as file:
        file.write(splothtml)
    sFileName

    # correct Arduino time if necessary
#    print "Now = ", today.strftime("%H:%M:%S"), " T=", tval
#    print today.strftime("%H:%M:%S"), " T=", tval
    if bPrintEachTemperature:
        print tval,
        iPrint += 1
        if (iPrint > 10):
            iPrint = 0
            print
    
    ist = sserial.find("T")
    # initial strings can be messed up
    totSecArdu = 0
    try:
        ih = int(sserial[ist+1:ist+3])
        im = int(sserial[ist+4:ist+6])
        isec = int(sserial[ist+7:ist+9])
        totSecArdu = (ih * 60 + im)*60 + isec
    except:
        totSecArdu = 0 
    totSecPi = (today.hour * 60 + today.minute)*60 + today.second
    delta = totSecArdu - totSecPi
    
#    print 'Tardu-Tpi:',delta
    app.tLastTimeSet.set(' dt=' + str(delta) + ' since ' + sLastSet)

    if (abs(delta) > 30):
        sLastSet = today.strftime("%H:%M:%S")
        sSend = 't' + today.strftime("%H:%M:%S") + '\n'
        ser.write(sSend)
        print "\nSent to Arduino: ", today.strftime("%b %d ") , sSend, ' Delta = ', delta

# get initial values from file:
if os.path.isfile(sFileDataName):
    with open(sFileDataName,"r") as file:
        textData = file.read()
        splitstr = textData.splitlines()
        # show 25 most recent
        splitstr.reverse()
        ilast = 25
        if ilast > len(splitstr):
            ilast = len(splitstr)
        for iline in range(ilast, -1 , -1):
            app.add_log(splitstr[iline] + '\n')

sMotionTime = ""
if os.path.isfile(sMovementName):
    with open(sMovementName,"r") as file:
        textData = file.read()
        splitstr = textData.splitlines()
        # show 25 most recent
        ilast = len(splitstr)
        ifirst = max(ilast - 25, 0)
        lastMotion = splitstr[ifirst:ilast]
        splitstr = None
        for aline in lastMotion:
            app.add_movement(aline + '\n')
            sMotionTime =  sMotionTime + aline + "<BR>\n"


            

# use fake read for test
# root.after(100, fakeread)
# after initializing serial, an arduino may need a bit of time to reset
root.after(100, readSerial)

root.mainloop()




    
