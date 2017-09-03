#!/usr/bin/python

from flask import Flask, render_template
import datetime
import os.path
#17-04-22 Use '/' for ReadThr html files

os.chdir('/home/pi/Devel/tmonitor')


app = Flask(__name__, static_url_path='/static')

#pi ip address is:http://192.168.0.105/
#pi can use localhost instead of ip address


sFileDataFormat = './templates/readTHRdata%d.txt'
sFileDataOut = './templates/data%d.html'

nRestarts = 0
g_timeString="none"

sprefix = """<!DOCTYPE HTML>
<html>
<head>
<title>Sensor %d data</title>
</head>
<h2>Sensor %d data</h2>
"""
spostfix = """
</html>
"""

def write_html(id):
       #Get last 10 lines
    nMaxLines = 50
    shtmlText = ""
    sFileDataName = sFileDataFormat % id
    if os.path.isfile(sFileDataName):
        with open(sFileDataName,"r") as file:
            # only read about 2 * 75 (assumes 50 - 100 char/line)
            nToRead = (nMaxLines+2) * 2 * 50
            file.seek(0, 2)
            flen = file.tell()
            file.seek(max(0, flen - nToRead))
            textData = file.read()
            splitstr = textData.splitlines()
            if len(splitstr) < nMaxLines+2:
                print ('** Warning ** Read ') + str(len(splitstr)) + ' lines'
            # show 25 most recent
            #splitstr.reverse()
            istart = len(splitstr) - nMaxLines
            if istart < 1:
                istart = 1
            showlines = splitstr[istart:]
            for sline in showlines:
                shtmlText += sline + "<BR>\n"
#    print(shtmlText)
    spre_adj = sprefix % (id, id)
    shtml = spre_adj + shtmlText + spostfix
    sFileHtml = sFileDataOut % id
    with open(sFileHtml,'w') as file:
        file.write(shtml)

@app.route("/d40")
def data40():
    write_html(40)
    return render_template('data40.html')

@app.route("/d41")
def data41():
    write_html(41)
    return render_template('data41.html')


@app.route("/info")
def hello():
    now = datetime.datetime.now()
    timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
    templateData = {
        'date' : timeString
    }
    try:
        return render_template('info.html', **templateData)
    except:
        return render_template('retry.html', **templateData)

@app.route("/inout")
def inout():
    now = datetime.datetime.now()
    timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
    templateData = {
        'date' : timeString
    }
    try:
        return render_template('ReadTh.html', **templateData)
    except:
        return render_template('retry.html', **templateData)

@app.route("/")
def inoutr_root():
    now = datetime.datetime.now()
    timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
    templateData = {
        'date' : timeString
    }
    try:
        return render_template('ReadThr.html', **templateData)
    except:
        return render_template('retry.html', **templateData)

@app.route("/inoutr")
def inoutr():
    now = datetime.datetime.now()
    timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
    templateData = {
        'date' : timeString
    }
    try:
        return render_template('ReadThr.html', **templateData)
    except:
        return render_template('retry.html', **templateData)
    
@app.route("/tplot")
def tplot():
    try:
        return render_template('tplot.html')
    except:
        now = datetime.datetime.now()
        timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
        templateData = {
            'date' : timeString
        }
        return render_template('retry.html', **templateData)

@app.route("/thplot")
def thplot():
    try:
        return render_template('thplot.html')
    except:
        now = datetime.datetime.now()
        timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
        templateData = {
            'date' : timeString
        }
        return render_template('retry.html', **templateData)

@app.route("/thrplot")
def thrplot():
    try:
        return render_template('thrplot.html')
    except:
        now = datetime.datetime.now()
        timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
        templateData = {
            'date' : timeString
        }
        return render_template('retry.html', **templateData)

@app.route("/stats")
def thrstats():
    cur_timeString = datetime.datetime.now().strftime("%I:%M:%S %p %a %b %d %Y" )
    return "At:{}<br><br>Restarts = {} since {}".format(cur_timeString, nRestarts, g_timeString)


if __name__ == "__main__":
    now = datetime.datetime.now()
    g_timeString = now.strftime("%I:%M:%S %p %a %b %d %Y" )
    for itry in range(1000):
        try:
            app.run(host='0.0.0.0',port=80,debug=True)
        except IOError:
            nRestarts += 1
            print 'IOError *** Restarts ***:', nRestarts
        else:
            print 'Error not handled'
            exit()

        
        
    
