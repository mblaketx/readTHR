#!/usr/bin/python

from flask import Flask, render_template
import datetime
import os.path
#17-04-22 Use '/' for ReadThr html files

os.chdir('/home/pi/Devel/tmonitor')


app = Flask(__name__, static_url_path='/static')

#pi ip address is:http://192.168.0.105/
#pi can use localhost instead of ip address

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



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80,debug=True)
    
