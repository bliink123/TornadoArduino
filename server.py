import tornado.ioloop
import tornado.web
import tornado.websocket
import threading
import math
import time
import random
import json
import serial # if you have not already done so
import pyowm
import urllib

PORT = 8888
SLEEP_TIME = 1

#ser = serial.Serial(port='COM3', baudrate= 9600)

key = '########APIKEY########'
location = 'Melbourne, AU'

class MainHandler(tornado.web.RequestHandler):
    """
    Initialises and creates the web template
    """
    def get(self):
        self.render("template.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self,application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
        self.writetobrowser = False
        self.buttonClickMessage = ""

    def write_data(self):
        self.temp_max, self.temp_message = weather()
        while self.writetobrowser:
            # Exercise for you overwrite the following with your own values
            # make the time be based off the users time
            #12:09PM on Sep 25, 2016
            datatosend = { 'number' : str(random.randrange(10,30)), 'date' : time.strftime("%I:%M on %b %d, %Y"), 'newvariable' : 'I have changed what the new variable says',
            'buttonClick' : self.buttonClickMessage, 'tempMax' : str(self.temp_max) + '°C', 'tempMessage' : self.temp_message, 'pyNum' : 49}
            self.write_message(datatosend)
            time.sleep(SLEEP_TIME)

    def open(self):
        print("WebSocket opened")
        if not self.writetobrowser:
            self.writetobrowser = True
            writerthread = threading.Thread(target=self.write_data, daemon=True)
            writerthread.start()

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        if message == "LEDOn":   #from template.html value="Button"
            print('LED Turned On!')
            self.buttonClickMessage = "LED Turned On!"
            ser.write(b'1')
            time.sleep(2)
            self.buttonClickMessage = ""
        elif message == "LEDOff":   #from template.html value="Button"
            print('LED Turned Off!')
            self.buttonClickMessage = "LED Turned Off!"
            ser.write(b'2')
            time.sleep(2)
            self.buttonClickMessage = ""
        else:
            print('Message from user: ' + message)
            #self.write_message(u"Received message from browser: " + message)

    def on_close(self):
        self.writetobrowser = False
        print("WebSocket closed")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", WebSocketHandler),
    ])

def weather():
    try:
        owm = pyowm.OWM(key)  # You MUST provide a valid API key
        observation = owm.weather_at_place(location)
        w = observation.get_weather()

        my_dict = w.get_temperature('celsius')
        temps = list((my_dict.values())) #seperates the values out of the dict into its own list
        temp_max = temps.pop(2) #seperate out the daily max temp
    except (urllib.error.HTTPError, pyowm.exceptions.unauthorized_error.UnauthorizedError):
        temp_max = 99
        temp_message = "Unable to get data from open weather map"

    if int(temp_max) > 20:
        temp_message = ('Temp is over 20°C: watering recommended')
    else :
        temp_message = ('Temp is under 20°C: no watering required')

    print(temp_max)
    print(temp_message)

    return (temp_max, temp_message)

def start_tornado():
    app = make_app()
    app.listen(PORT)
    tornado.ioloop.IOLoop.current().start()

def stop_tornado():
    tornado.ioloop.IOLoop.current().stop()

def start():
    start_tornado()


if __name__ == "__main__":
    start()
