import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.options
from tornado.options import define, options
import os.path
import threading
import math
import time
import random
import json
import serial
import pyowm
import urllib

PORT = 8888
SLEEP_TIME = 1

#ser = serial.Serial(port='COM3', baudrate= 9600)

with open('keyfile.txt', 'r') as keyfile:
    key = keyfile.read()
location = 'Melbourne, AU'

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("template.html")

class AboutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("about.html")

class LoginHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return
        self.render('login.html')

    @tornado.gen.coroutine
    def post(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>blocked</center>')
            return
        
        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))
        if "admin" == getusername and "password" == getpassword:
            self.set_secure_cookie("user", self.get_argument("username"))
            self.set_secure_cookie("incorrect", "0")
            self.redirect(self.reverse_url("main"))
        else:
            incorrect = self.get_secure_cookie("incorrect") or 0
            increased = str(int(incorrect)+1)
            self.set_secure_cookie("incorrect", increased)
            self.write("""<center>
                            Something Wrong With Your Data (%s)<br />
                            <a href="/">Go Home</a>
                          </center>""" % increased)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", self.reverse_url("main")))

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
            datatosend = { 'ranNum' : str(random.randrange(10,30)),
                           'date' : time.strftime("%I:%M%p on %b %d, %Y"),
                           'newvariable' : 'I have changed what the new variable says',
                           'buttonClick' : self.buttonClickMessage,
                           'tempMax' : str(self.temp_max) + '°C',
                           'tempMessage' : self.temp_message,
                           'pyNums' : [random.randrange(10, 30) for x in range(7)]}
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

def weather():
    try:
        owm = pyowm.OWM(key)  # You MUST provide a valid API key
        observation = owm.weather_at_place(location)
        w = observation.get_weather()

        my_dict = w.get_temperature('celsius')
        temps = list((my_dict.values())) #seperates the values out of the dict into its own list
        temp_max = temps.pop(2) #seperate out the daily max temp
        if int(temp_max) > 20:
            temp_message = ('Temp is over 20°C: watering recommended')
        else :
            temp_message = ('Temp is under 20°C: no watering required')
    except (urllib.error.HTTPError, pyowm.exceptions.unauthorized_error.UnauthorizedError):
        temp_max = 99
        temp_message = "Unable to get data from open weather map"

    return (temp_max, temp_message)

class Application(tornado.web.Application):
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "login_url": "/login",
            'template_path': os.path.join(base_dir, "templates"),
            'static_path': os.path.join(base_dir, "templates/static"),
            'debug':True,
            "xsrf_cookies": True,
        }
        
        tornado.web.Application.__init__(self, [
            tornado.web.url(r'/', MainHandler, name="main"),
            tornado.web.url(r'/websocket', WebSocketHandler),
            tornado.web.url(r'/login', LoginHandler, name="login"),
            tornado.web.url(r'/logout', LogoutHandler, name="logout"),
            tornado.web.url(r'/about', AboutHandler, name="about"),
        ], **settings)

def start_tornado():
    tornado.options.parse_command_line()
    Application().listen(PORT)
    tornado.ioloop.IOLoop.current().start()

def stop_tornado():
    tornado.ioloop.IOLoop.current().stop()

def start():
    start_tornado()


if __name__ == "__main__":
    start()

