from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import time
import sys
import socket
import random
import smtplib
from email.message import EmailMessage
import requests
import json
import random
from googletrans import Translator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import pytz
import importlib.util

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

JSON_FILE_OF_STRINGS = "insert here the location of the JSON file. must be in the same dir as server_mirror.py"
DICT_OF_STRINGS = None

TRANSLATOR = Translator()

OPTIONS = webdriver.ChromeOptions()
OPTIONS.add_argument("headless")
BROWSER = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=OPTIONS) # change webdriver for different OS

class server_class():
    def __init__(self, encrypter):
        """ The function makes an instace of the class. """
        self.server_socket = None
        self.client_socket = None
        self.address = None

        self.encrypter = encrypter
        
        self.ip = '0.0.0.0'
        self.port = 8878

    def create_server_socket(self):
        """ The function creates the server. """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))

    def connect_server(self):
        """ The function connects the client to the server. """
        self.server_socket.listen(1)
        self.client_socket, self.address = self.server_socket.accept()

    def close_server(self):
        """ The function disconnects from from the client and closes itself. """
        self.server_socket.close()
        self.client_socket.close()

    def receive_msg(self):
        """ The function recieves a message from the client and return it decoded and decrypted. """
        etext = self.client_socket.recv(1024)
        return self.encrypter.decrypt_message(etext).lower()

    def send_msg(self, text):
        """ The function sends a message to the client, encoded and decrypted. """
        etext = self.encrypter.encrypt_message(text)
        self.client_socket.send(etext)

def module_from_file(module_name, file_path):
    """ The function allows a module from a different file to be used. """
    """taken shamlessly from -> https://stackoverflow.com/a/51585877"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def extract_info_from_json_file():
    """ The function reads the information from the JSON file called server_side_function_strings.json """
    global DICT_OF_STRINGS
    global JSON_FILE_OF_STRINGS
    with open(JSON_FILE_OF_STRINGS) as sf: # sf == server_file
        DICT_OF_STRINGS = json.load(sf)

def authenticate_google_calender():
    # Shows basic usage of the Google Calendar API.

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

def get_events(day, service):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)
    
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return 'No events found.'
    else:
        if len(events)>1:
            text_to_say = f"You have {len(events)} events on this day. They are "
        else:
            text_to_say = f"You have one event on this day. It is "
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_time = str(start.split("T")[1].split("+")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else:
                start_time = f"{str(int(start_time.split(':')[0]) - 12)}:{start_time.split(':')[1]} pm"

            text_to_say += f"{event['summary']} at {start_time}. "

        return text_to_say

def send_sos_mail():
    """The function sends an email to a list of contacts. """
    try:
        now = str(datetime.datetime.now()).split(".")[0]
        msg = EmailMessage()
        msg['Subject'] = "SOS ACTIVATED BY SOMEONE"
        msg["From"] = DICT_OF_STRINGS['ALEX_CREDENTIALS']['email_address']
        msg["To"] = DICT_OF_STRINGS['SOS_CONTACTS']
        msg.set_content(
            f"Someone Activated the SOS Feature in the Alex Smart Mirror at {now}\nPlease check to see if everything is OK!")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(DICT_OF_STRINGS['ALEX_CREDENTIALS']["email_address"], DICT_OF_STRINGS['ALEX_CREDENTIALS']["email_password"])
            smtp.send_message(msg)
        return "message sent!"
    
    except Exception as e:
        print(e)
        return "I couldn't do that for some reason."


def get_date_from_text(text):
    """ The function gets a string of text and retives a date from it. """
    # datetime.date.today().weekday() works like this

    # monday, tuesday, wednesday, thursday, friday, saturday, sunday
    #    0       1         2           3       4        5       6
    text = text.lower().split()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today
    """
    need to check edge cases --> if 31 of a month, need to update month (and year if needed)
                                 and other cases...

    elif text.count("the day after tommorow") > 0:
        return datetime.date(month=today.month, day=(today.day + 2), year=today.year)
    elif text.count("tomorrow") > 0:
        return datetime.date(month=today.month, day=(today.day + 1), year=today.year)
    elif text.count("yesterday") > 0:
        return datetime.date(month=today.month, day=(today.day - 1), year=today.year)
        
    else:"""
    day_of_month = -1
    day_of_week = -1
    month = -1
    year = today.year

    for w in text:
        if w in DICT_OF_STRINGS['MONTHS']:
            month = DICT_OF_STRINGS['MONTHS'].index(w) + 1
        elif w in DICT_OF_STRINGS['DAYS']:
            day_of_week = DICT_OF_STRINGS['DAYS'].index(w)
        elif w.isdigit():
            day_of_month = int(w)
        else:
            for extension in DICT_OF_STRINGS['DAY_EXTENSIONS']:
                found = w.find(extension)
                if found > -1:
                    try:
                        day_of_month = int(w[:found])
                    except:
                        pass

    if (month != -1) and (month < today.month):
        # if the month mentioned is before the current month set the year to the next
        year += 1
    if (month == -1) and (day_of_month != -1):
        # if we didn't find a month, but we have a day
        if day_of_month < today.day:
            # if the day of the month is less then today then the month is the next month
            month = today.month + 1
        else:
            month = today.month
    if (month == -1) and (day_of_week != -1):
        # if we only have a day of the week. like => wednesday/friday...
        this_day_of_the_week = today.weekday()
        difference = day_of_week - this_day_of_the_week
        if difference < 0:
            difference += 7
        if (text.count("next") > 0) or (text.count("following") > 0):
            difference += 7

        return today + datetime.timedelta(difference)

        if day_of_month != -1:
            return datetime.date(month=month, day=day_of_month, year=year)


def get_time():
    """ The function returns the current time in a 12 hour format. """
    time = str(datetime.datetime.now().time())
    if int(time.split(":")[0]) < 12:
        time = time[:5] + "am"  # to 8 if you want seconds
    elif int(time.split(":")[0]) == 12:
        time = time[:5] + "pm"  # to 8 if you want seconds
    else:
        time_h = str(int(time.split(":")[0]) - 12)
        time = time_h + time[2:5] + " pm"  # to 8 if you want seconds
    return time


def get_current_date():
    """ The function returns the current date. """
    today = datetime.date.today()
    return f"Today's date is {today}"


def get_weather(text):
    """ The function gets a string and searches the internet for an answer. It then reads the page, orgenizes a good answer and returns it. """
    try:
        source = requests.get(f"https://www.google.com/search?q={text}").text
        soup = bs(source, 'html.parser')
        place = soup.find('div', class_="kCrYT")
        place = place.find('span', class_="BNeawe tAd8D AP7Wnd").text
        place = TRANSLATOR.translate(place).text

        temp = soup.find_all('div', class_="BNeawe iBp4i AP7Wnd")
        temp = temp[1].text
        temp = temp[:len(temp)-1]

        info = soup.find_all('div', class_="BNeawe tAd8D AP7Wnd")[1]
        a = ''
        for i in range(3, 7):
            try:
                a += f"{info.text.split()[i]} "
            except:
                pass

        info = TRANSLATOR.translate(a).text

        return (f"The current weather in {place} is {temp}. {info}")
    except:
        return "I couldn't do that for some reason."

def get_alarm_time(text):
    """ The function gets a string of text, and retrives the specific time an alarm needs to go off, according to the text. """
    text = text.lower().split()
    now = datetime.datetime.now().time()

    alarm_seconds = 0
    alarm_minutes = 0
    alarm_hours = 0

    if "second" in text:
        alarm_seconds = now.second + int(text[text.index("second") - 1])
    elif "seconds" in text:
        alarm_seconds = now.second + int(text[text.index("seconds") - 1])
    else:
        alarm_seconds = now.second
    if alarm_seconds > 59:
        how_many_full_minutes = alarm_seconds // 60
        alarm_seconds = (alarm_seconds % 60)
        alarm_minutes += how_many_full_minutes

    if "minute" in text:
        alarm_minutes += now.minute + int(text[text.index("minute")-1])
    elif "minutes" in text:
        alarm_minutes += now.minute + int(text[text.index("minutes")-1])
    else:
        alarm_minutes += now.minute
    if alarm_minutes > 59:
        how_many_full_hours = alarm_minutes // 60
        alarm_minutes = (alarm_minutes % 60)
        alarm_hours += how_many_full_hours

    if "hour" in text:
        alarm_hours += now.hour + int(text[text.index("hour")-1])
    elif "hours" in text:
        alarm_hours += now.hour + int(text[text.index("hours") - 1])
    else:
        alarm_hours += now.hour
    if alarm_hours > 23:
        alarm_hours -= 24
        
    return datetime.time(alarm_hours, alarm_minutes, alarm_seconds)

def add_to_known_facts(text):
    """ The function gets a string and backs it up in the JSON file. """
    with open(JSON_FILE_OF_STRINGS) as f:
        temp_dict = json.load(f)

    if text not in temp_dict["KNOWN_FACTS"]:
        temp_dict['KNOWN_FACTS'].append(text)

    with open(JSON_FILE_OF_STRINGS, 'w') as f:
        json.dump(temp_dict, f, indent=4)

        
def get_a_known_fact():
    """ The function gets a random fact from a backup in the JSON file. """
    with open(JSON_FILE_OF_STRINGS) as f:
        temp_dict = json.load(f)

    known_jokes = temp_dict['KNOWN_FACTS']
    random_num = random.randint(0, len(known_jokes)-1)
    return known_jokes[random_num]


def get_random_fact():
    """ The function scrapes the web for a random fact. If it finds one, it backs it up in the JSON file. Else, it gets a random fact from the JSON file. """
    try:
        source = requests.get("http://randomfactgenerator.net/").text
        soup = bs(source, 'html.parser')
        facts = soup.find_all('div', id='z')
        formatted_facts = []
        for i in facts:
            a = i.text.split('\n')[0]
            formatted_facts.append(a)

        random_num = random.randint(0, len(formatted_facts) - 1)
        fact = formatted_facts[random_num]
        add_to_known_facts(fact)
        return fact
    except:
        return get_a_known_fact()

def add_to_known_jokes(text):
    """ The function gets a string and backs it up in the JSON file. """
    with open(JSON_FILE_OF_STRINGS) as f:
        temp_dict = json.load(f)
    if text not in temp_dict["KNOWN_JOKES"]:
        temp_dict["KNOWN_JOKES"].append(text)

    with open(JSON_FILE_OF_STRINGS, 'w') as f:
        json.dump(temp_dict, f, indent=4)

def get_a_known_joke():
    """ The function gets a random fact from a backup in the JSON file. """
    with open(JSON_FILE_OF_STRINGS) as f:
        temp_dict = json.load(f)

    known_jokes = temp_dict['KNOWN_JOKES']
    random_num = random.randint(0, len(known_jokes)-1)
    return known_jokes[random_num]

def get_random_joke():
    """ The function scrapes the web for a random joke. If it finds one, it backs it up in the JSON file. Else, it gets a random fact from the JSON file. """
    try:
        BROWSER.get("https://edition.cnn.com/interactive/2019/06/us/dad-joke-generator-trnd/")
        button = WebDriverWait(BROWSER, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.interactive-container > div.machine-container > div > div > div")))
##      the line above waits for 5 seconds until there is a button to push
        button.click()
        joke = WebDriverWait(BROWSER, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.interactive-container > div.machine-output-area > div"))).text
##      the line above waits for 5 seconds until there is a joke to read
        BROWSER.quit()
        add_to_known_jokes(joke)
        return(joke)
    except:
        return get_a_known_joke()


def answering_func(text, service):
    """ This function recieves a string and service (nessecary for the google functions) and tries to find an answer by trying to see if the question matches a catagory in the JSON file. """
    did_something = False
    for phrase in DICT_OF_STRINGS['EXIT_STRINGS']:
        # doesn't need a LAST_SAID because if we got here the system will exit
        if phrase in text:
            did_something = True
            if phrase == "see you later alligator":
                return f"{DICT_OF_STRINGS['EXIT_MESSAGES'][-1]}#STOP_NOW"
            else:
                length = len(DICT_OF_STRINGS['EXIT_MESSAGES'])
                random_num = random.randint(0, length - 2) # length -2 because i don't want it to get to the response "in a while crocodile"
                text = DICT_OF_STRINGS['EXIT_MESSAGES'][random_num]
                return f"{text}#STOP_NOW"

    for phrase in DICT_OF_STRINGS['SOS_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            msg = send_sos_mail()
            return msg

    for phrase in DICT_OF_STRINGS['CALENDAR_STRINGS']:
        if (phrase in text) and (did_something is not True):
            date = get_date_from_text(text)
            if date:
                text_to_say = get_events(date, service)
                did_something = True
                return text_to_say
            else:
                text = DICT_OF_STRINGS['I_DIDNT_UNDERSTAND']
                did_something = True
                return text

    for phrase in DICT_OF_STRINGS['TIME_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            current_time = get_time()
            return current_time

    for phrase in DICT_OF_STRINGS['DATE_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            current_date = get_current_date()
            return current_date

    for phrase in DICT_OF_STRINGS['WHAT_CAN_YOU_DO_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            text = DICT_OF_STRINGS['WHAT_CAN_I_DO']
            return text

    for phrase in DICT_OF_STRINGS['WEATHER_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            current_weather = get_weather(text)
            return current_weather

    for phrase in DICT_OF_STRINGS['RANDOM_FACT_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            random_fact = get_random_fact()
            return random_fact

    for phrase in DICT_OF_STRINGS['RANDOM_JOKE_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            joke = get_random_joke()
##            joke = f"JK+{joke}"
            return joke

    for phrase in DICT_OF_STRINGS['ALARM_STRINGS']:
        if (phrase in text) and (did_something is not True):
            did_something = True
            text = text[len(phrase)+1:]
            alarm_time = get_alarm_time(text)
            alarm_time = f"AT+{alarm_time}"
            return alarm_time

    if did_something is False:
        text = DICT_OF_STRINGS['I_DIDNT_UNDERSTAND']
        return text


def answering_loop(server, service):
    """ This function recieves the server object and service. It then recieves a question from the client and calls answering_func on it. If the answer relates to dissconecting, the function will dissconnect. """
    while True:
        text = server.receive_msg()
        answer = str(answering_func(text, service))
        if answer[len(answer)-9:] == "#STOP_NOW":
            answer = answer[:len(answer)-9]
            server.send_msg(answer)
            return "STOP"
        else:
            print(answer)
            server.send_msg(answer)

def setting_up_the_server():
    """ The function sets up the server by importing the encryption module, connecting to the google API and creating the server instance. It returns the encryption object, the server object and service. """
    start_time = time.time()
    encryption_object = module_from_file("encryption_object", "/home/pi/Desktop/encryption_object.py") # change dir if needed
    encrypter = encryption_object.enc_dec()
    server = server_class(encrypter)
    server.create_server_socket()
    service = authenticate_google_calender()
    server.create_server_socket()
    extract_info_from_json_file()
    end_time = time.time()
    setup_time = end_time-start_time
    return service, server, setup_time

def main():
    """ This function is the main function that builds the server. """
    service, server, setup_time = setting_up_the_server()
    print("server is up")
    print(f"it took {setup_time} seconds")
    server.connect_server()
    stop = answering_loop(server, service)
    if stop is "STOP":
        server.close_server()

if __name__ == '__main__':
    main()

