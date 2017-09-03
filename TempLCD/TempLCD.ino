/**************************************************************************/
/*!
This is a demo for the Adafruit MCP9808 breakout
----> http://www.adafruit.com/products/1782
Adafruit invests time and resources providing this open source code,
please support Adafruit and open-source hardware by purchasing
products from Adafruit!
*/
/**************************************************************************/
/***************
This uses serial input of the form tHH:MM:SS to adjust the time display
on the LCD so it matches the entered time
***************/

#include <Wire.h>
#include "Adafruit_MCP9808.h"
#include <LiquidCrystal.h>

int inputPin=2;
int ival = 0;
int ivalOld = 0;

// Create the MCP9808 temperature sensor object
Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(7, 8, 9, 10, 11, 12);

String inputString = "";         // a string to hold incoming data
long lSecOffset = 0; //Offset to make time display correct

float doldf = 0.0;
float dtmax = -100;
long tmax = 0;
float dtmin = 200;
long tmin = 0;
int bmaxtime = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("MCP9808 demo");
  
  lcd.begin(16, 2);
  
  // Make sure the sensor is found, you can also pass in a different i2c
  // address with tempsensor.begin(0x19) for example
  if (!tempsensor.begin()) {
    Serial.println("Couldn't find MCP9808!");
    while (1);
  }
  lcd.print("                ");
}

void loop() {
  //Serial.println("wake up MCP9808.... "); // wake up MSP9808 - power consumption ~200 mikro Ampere
  ival = digitalRead(inputPin);
  lcd.setCursor(15, 0);
  if (ival) {
      lcd.print("*");
  } else {
      lcd.print(" ");
  }   
  tempsensor.shutdown_wake(0);   // Don't remove this line! required before reading temp

  // Read and print out the temperature, then convert to *F
  float c = tempsensor.readTempC();
  float f = c * 9.0 / 5.0 + 32;
  // String sf = floatToStr(f, 1);

  long lsec = millis()/1000 + lSecOffset;
   
  // Only print changes Temperature or Motion
  if (doldf != f || ival != ivalOld) {
    doldf = f;
    ivalOld = ival;
    if (f > dtmax) {
      dtmax = f;
      tmax = lsec;
    }
     if (f < dtmin) {
      dtmin = f;
      tmin = lsec;
    }
    Serial.print(ival);
    Serial.print(" T");
    
    String shms = sHMS(lsec);
    Serial.print(shms);
    Serial.print(" Temp: ");
    Serial.print(f); Serial.println("*F");
  }
  delay(250);
  
  //Serial.println("Shutdown MCP9808.... ");
  tempsensor.shutdown_wake(1); // shutdown MSP9808 - power consumption ~0.1 mikro Ampere
  
  delay(2000-250);
  
  // Update LCD display each time
  
  String shms = sHMS(lsec);
  
  lcd.setCursor(0,0);
  lcd.print(shms);
  lcd.print(" <");
  String sdtmin = floatToStr(dtmin,1);
  lcd.print(sdtmin);
  
  lcd.setCursor(0, 1);
  String sf = floatToStr(f, 1);
  lcd.print(sf);
  lcd.print(">");
  String sdtmax = floatToStr(dtmax,1);
  lcd.print(sdtmax);
  if (bmaxtime) {
    lcd.print(">");   
    String shm = sHM(tmax);
    bmaxtime = 0;
    lcd.print(shm);
 //   Serial.print(shm); Serial.print(">"); Serial.println(tmax);
  } else {
    lcd.print("<");   
    String shm = sHM(tmin);
    bmaxtime = 1;
    lcd.print(shm);
//    Serial.print(shm); Serial.print("<"); Serial.println(tmin);
  }
}

// Convert seconds to HH:MM:SS
String sHMS(long sec)
{
  int asec = sec % 60;
  sec /= 60;
  int amin = sec % 60;
  int ahour = sec/60;
  char cbuf[20];
  int nch = sprintf(cbuf, "%2d:%2d:%2d", ahour, amin, asec);
  String sret = cbuf;
  return sret;
}

// Convert seconds to HH:MM:SS
String sHM(long sec)
{
  int asec = sec % 60;
  sec /= 60;
  int amin = sec % 60;
  int ahour = sec/60;
  char cbuf[20];
  int nch = sprintf(cbuf, "%2d%2d", ahour, amin);
  String sret = cbuf;
  return sret;
}

  
void processString(String sInput)
{
  if (sInput[0] == 't' && sInput[3] == ':') {
    Serial.print(sInput);
  } else {
    Serial.println("skipped");
    return;
  }
  long iH = sInput.substring(1,3).toInt();
  long iM = sInput.substring(4,6).toInt();
  long iS = sInput.substring(7,9).toInt();
 
  long lsec = (iH * 60 + iM) * 60 + iS;
  Serial.print(lsec);
  Serial.print(" gives ");
  Serial.println(sHMS(lsec));
  
  long lTicks = millis()/1000;
  lSecOffset = lsec - lTicks;
}

/*
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      processString(inputString);
      // clear the string:
      inputString = "";       
    }
  }
}

// helper to convert a float value to a string with given number of decimals after period
// Rounds
String floatToStr(float f, int decims) {
  float mult = 1.0;
  int l = decims;
  while (l > 0) {
    mult = mult * 10.0;
    l--;
  }
  int v = (f * mult + .5); // Round
  String res = String(v);
  if (decims != 0) {
    l = res.length();
    int p = l - decims;
    if (p <= 0) {
      res = "0." + res;
    } else {
      String intStr = res.substring(0, p);
      String decStr = res.substring(p);
      res = intStr + "." + decStr;
    }
  }
  return res;
}


