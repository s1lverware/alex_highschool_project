from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtWidgets import QApplication, QLCDNumber
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from PyQt5 import QtCore
import time
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import QTime, QTimer
import socket
import datetime
import json
import os
import speech_recognition as sr
import random
import sys
import threading
from PyQt5.QtWidgets import QApplication, QLCDNumber
import vlc
import importlib.util

HOST = '127.0.0.1'
PORT = 8878

def module_from_file(module_name, file_path):
    """ The function allows a module from a different file to be used. """
    """taken shamlessly from -> https://stackoverflow.com/a/51585877"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class client_class():
    def __init__(self, encrypter):
        """ The function creates an instances of the class. """
        self.my_socket = None
        self.encrypter = encrypter
        self.host = '127.0.0.1'
        self.port = 8878

    def create_client_and_connect(self):
        """ The function creates the client and connects to the server. """
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.connect((self.host, self.port))

    def send_message(self, text):
        """ The function recievs a string that needs to be sent to the server. 
        It encrypts it, encodes it and sends it to the server. """
        self.my_socket.send(self.encrypter.encrypt_message(text))

    def receive_message(self):
        """ The function waits for the server to send an answer. It then recieves it, 
        decrypts it, and decodes it. Later, it returns the result. """
        return self.encrypter.decrypt_message(self.my_socket.recv(1024))

    def close_client(self):
        """ The function disconnects from the server. """
        self.my_socket.close()

class alex_main_window(QMainWindow):
    def __init__(self, client):
        """ The function creates an instance of the class, 
        and calls init_UI, that sets up the window. """
        super(alex_main_window, self).__init__()
        self.title = "I'm Alex"

        self.client = client
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # The thing above removes the title bar. Taken shamelessly from https://stackoverflow.com/questions/7021502/pyqt-remove-the-programs-title-bar
        self.left_window = 0
        self.top_window = 0
        self.height_window = 1360
        self.width_window = 768

        self.the_one_and_only_mic = 0

        self.last_said_text = "lol + troll = life"
        self.did_something = False
        self.is_speaking = False
        self.playing_alarm = False

        self.answers_text = QLabel(self)
        self.answer_font = QtGui.QFont("Arial", 34)

        self.clock_window = QLCDNumber(self)

        self.json_file_of_main_strings = "/home/pi/Desktop/client_side_function_strings.json" # change dir if needed
        self.dict_of_main_strings = None

        self.init_UI()

    def init_UI(self):
        """ The function initializes the main window and the client. """
        self.calibrate_pi_mic()
        self.extract_info_from_json_file()

        self.setWindowTitle(self.title)
        self.setGeometry(self.left_window, self.top_window, self.height_window, self.width_window)
        self.setStyleSheet("background: black")

        self.answers_text.setGeometry(120, 468, 300, 300)
        self.answers_text.setStyleSheet(self.dict_of_main_strings['LIGHT_OFF_TEXT_STYLE'])
        self.answers_text.setFont(self.answer_font)

        self.clock_window.setSegmentStyle(QLCDNumber.Filled)
        self.clock_window.setStyleSheet(self.dict_of_main_strings['LIGHT_OFF_TEXT_STYLE'])
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.showTime()
        self.clock_window.resize(400, 150)
        self.clock_window.move(10, 15)

        self.show()
        main_thread = threading.Thread(target=self.start_function, args=())
        main_thread.start()

    def extract_info_from_json_file(self):
        """ The function reads data from the JSON file. """
        with open(self.json_file_of_main_strings, "r") as cf:  # cf==client_file
            self.dict_of_main_strings = json.load(cf)

    def calibrate_pi_mic(self):
        """ The function searches for the index of the right microphone. """
        avilable_microphones = []
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if name == "USB Device 0x46d:0x89d: Audio (hw:1,0)":
                self.the_one_and_only_mic = index

    def turn_light_on(self):
        """ The function switches the color scheme to light mode. """
        self.setStyleSheet("background: white")
        self.clock_window.setStyleSheet(self.dict_of_main_strings['LIGHT_ON_TEXT_STYLE'])
        self.answers_text.setStyleSheet(self.dict_of_main_strings['LIGHT_ON_TEXT_STYLE'])
        length = len(self.dict_of_main_strings['LIGHT_ON_TEXT_TO_SPEAK'])
        random_num = random.randint(0, length - 1)
        answer = self.dict_of_main_strings['LIGHT_ON_TEXT_TO_SPEAK'][random_num]
        self.speak(answer)
        self.last_said_text = answer

    def turn_light_off(self):
        """ The function switches the color scheme to light mode. """
        self.setStyleSheet("background: black")
        self.clock_window.setStyleSheet(self.dict_of_main_strings['LIGHT_OFF_TEXT_STYLE'])
        self.answers_text.setStyleSheet(self.dict_of_main_strings['LIGHT_OFF_TEXT_STYLE'])
        length = len(self.dict_of_main_strings['LIGHT_OFF_TEXT_TO_SPEAK'])
        random_num = random.randint(0, length - 1)
        answer = self.dict_of_main_strings['LIGHT_OFF_TEXT_TO_SPEAK'][random_num]
        self.speak(answer)
        self.last_said_text = answer

    def showTime(self):
        """ The function is responsible for creating and showing the digital clock. """
        """taken shamelessly from here
        https: // github.com / baoboa / pyqt5 / blob / master / examples / widgets / digitalclock.py

        also used things from here
        https://doc.qt.io/qt-5/qtimer.html#details
        https://stackoverflow.com/questions/48168432/adding-a-simple-clock-to-a-gui
        """

        time = QTime.currentTime()
        text = time.toString('hh:mm')
        if (time.second() % 2) == 0:
            text = text[:2] + ' ' + text[3:]

        self.clock_window.display(text)

    def start_function(self):
        """ This function calls the main loop and stops the client if nessicary. """
        stop = self.main_loop()
        if stop == "STOP":
            self.client.close_client()
            time.sleep(5)
            self.close_gui()

    def close_gui(self):
        """ The function closes the window. """
        self.close()

    def enter_enters(self, text):
        """ This function calculates how many new lines should be in the text on the screen, and puts them there. """
        how_many_enters = len(text)//48 + 1 # because I want about 48 characters in a line
        new_text = []
        start_of_line = 0

        for enter in range(how_many_enters):
            if (enter+1)*48 > len(text):
                new_text.append(text[start_of_line:len(text)])
            else:
                if text[(enter+1)*48] == " ":
                    end_of_line = (enter+1)*48
                else:
                    current_char = (enter+1)*48
                    while text[current_char] != " ":
                        current_char += 1
                        if current_char >= len(text):
                            break
                    end_of_line = current_char
                new_text.append(text[start_of_line:end_of_line])
                start_of_line = end_of_line + 1
                if (enter + 1) < how_many_enters:
                    new_text.append("\n")

        return "".join(new_text)

    def remove_apostrophe(self, text):
        """ This function removes apostrophes from the text. 
        This has to be done because of the way the speaking function is coded. """
        return text.replace(r"'", "")

    def speak(self, text):
        """ The function checks that the alarm isn't on, that the text isn't None or "waiting", 
        checks to see if new lines are needed, places them if nessecary, writes the text to a text box and speaks the text. """
        while self.playing_alarm:
            pass
        self.is_speaking = True
        if text is not None:
            print(text)
            if text != "waiting":
                if len(text) > 48:
                    new_text = self.enter_enters(text)
                    self.answers_text.setText(new_text)
                else:
                    self.answers_text.setText(text)
                self.answers_text.adjustSize()
                os.system(f"espeak -ven-us '{self.remove_apostrophe(text)}' 2>/dev/null")
        self.is_speaking = False

    def listen(self):
        """ The function listens to the user through the mic we want. After it hears speaking, 
        it sends the audio to a google API for speech recognition, recieves the transcribed text, 
        and returns it to the user. """
        r = sr.Recognizer()
        with sr.Microphone(device_index=self.the_one_and_only_mic) as source:
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source)
            try:
                transcribed_text = r.recognize_google(audio)
                return transcribed_text
            except Exception as e:
                print(f"Error: {str(e)}")
                return ""

    def check_for_wake_phrase(self, text):
        """ The function recives a string and checks if someone addressed Alex. 
        If true, it returns True. Else, it returns False. """
        for phrase in self.dict_of_main_strings['WAKE_PHRASE']:
            if phrase in text:
                return True
        return False

    def remove_wake_phrase(self, text):
        """ The function recieves a string, removes the wake phrase from the it and returns the new text. """
        for phrase in self.dict_of_main_strings['WAKE_PHRASE']:
            if phrase in text:
                length_phrase = len(phrase) + 1
                text = text[length_phrase:]
                return text

    def find_answer_swear_words(self, text):
        """ Finds an answer if someone addressed Alex with swear words. """
        for phrase in self.dict_of_main_strings['SWEAR_WORDS']:
            if phrase in text:
                self.did_something = True
                length = len(self.dict_of_main_strings['SWEAR_WORDS_ANSWERS'])
                random_num = random.randint(0, length - 1)
                answer = self.dict_of_main_strings['SWEAR_WORDS_ANSWERS'][random_num]
                self.speak(answer)
                self.last_said_text = answer
            else:
                self.speak(None)

    def find_answer_other_voice_assistants(self, text):
        """ The function finds an answer if the user addressed another voice assistant. """
        for phrase in self.dict_of_main_strings['OTHER_VOICE_ASSISTANTS']:
            if phrase in text:
                self.did_something = True
                if phrase == "jarvis":
                    length = len(self.dict_of_main_strings['JARVIS_RESPONSE'])
                    random_num = random.randint(0, length - 1)
                    answer = self.dict_of_main_strings['JARVIS_RESPONSE'][random_num]
                else:
                    answer = self.dict_of_main_strings['OTHER_VOICE_ASSISTANTS_RESPONSE']
                self.speak(answer)
                self.last_said_text = answer
            else:
                self.speak(None)

    def find_answer_how_to_call_me(self, text):
        """ The function answers the users question "how to call me?". """
        for phrase in self.dict_of_main_strings['HOW_TO_CALL_ME']:
            if phrase in text:
                self.did_something = True
                length = len(self.dict_of_main_strings['HOW_TO_CALL_ME_RESPONSE'])
                random_num = random.randint(0, length - 1)
                answer = self.dict_of_main_strings['HOW_TO_CALL_ME_RESPONSE'][random_num]
                self.speak(answer)
                self.last_said_text = answer
            else:
                self.speak(None)

    def start_alarm(self, text):
        """ The function recieves the time of the alarm, and checks when time's up and then starts the alarm. """
        alarm_time = text
        print(alarm_time)
        now = datetime.datetime.now().time()

        while int(alarm_time[:2:]) > now.hour:
            now = datetime.datetime.now().time()

        while int(alarm_time[3:5]) > now.minute:
            now = datetime.datetime.now().time()

        while int(alarm_time[6:]) > now.second:
            now = datetime.datetime.now().time()

        while self.is_speaking:  # so that the timer will be heared and not overrun by the speak function.
            pass
        self.playing_alarm = True
        self.rickroll()
        self.playing_alarm = False

    def rickroll(self):
        """ The function plays a song for 15 seconds. """
        player = vlc.MediaPlayer('/home/pi/Music/rickroll_but_it_never_starts.mp3') # change the sounds to your liking
        player.play()
        time.sleep(15)
        player.stop()

    def get_last_said(self, text):
        """ The function recieves text, checks if it matches the catagory of lst_said. 
        If it does, then it says the last said string. Else, is does nothing. """
        for phrase in self.dict_of_main_strings['LAST_SAID_STRINGS']:
            if phrase in text:
                self.did_something = True
                self.speak(self.last_said_text)
            else:
                self.speak(None)

    def turn_the_light_on(self, text):
        """ The function recieves text and checks if the text matches the catagory. 
        If so, it changes color scheme. Else, it doesn't. """
        for phrase in self.dict_of_main_strings['LIGHT_ON_TEXT']:
            if phrase in text:
                self.did_something = True
                self.turn_light_on()

    def turn_the_light_off(self, text):
        """ The function recieves text and checks if the text matches the catagory. 
        If so, it changes color scheme. Else, it doesn't. """
        for phrase in self.dict_of_main_strings['LIGHT_OFF_TEXT']:
            if phrase in text:
                self.did_something = True
                self.turn_light_off()

    def check_basics(self, text):
        """ This function checks the basic functions of the client 
        and answers "thank you", "sorry" and "how are you". """
        self.find_answer_swear_words(text)
        self.find_answer_other_voice_assistants(text)
        self.find_answer_how_to_call_me(text)
        self.get_last_said(text)
        self.turn_the_light_on(text)
        self.turn_the_light_off(text)

        if (text.count("thanks") > 0) or (text.count("thank you") > 0):
            self.did_something = True
            answer = "you're welcome"
            self.speak(answer)
            self.last_said_text = answer

        elif text.count("sorry") > 0:
            self.did_something = True
            answer = "It's ok. Just don't do it again."
            self.speak(answer)
            self.last_said_text = answer

        elif text.count("how are you") > 0:
            self.did_something = True
            answer = "I am great! How are you?"
            self.speak(answer)
            self.last_said_text = answer

    def main_loop(self):
        """ This is the main function of the client. 
        This function listens to the user and tries to answer the question.
        If it can't then it will send the wuestion to the server, 
        wait for the response, read it out loud, and acts if nessicary. """
        while True:
            self.did_something = False
            self.speak("waiting")
            text = self.listen().lower()
            print(text)

            self.check_basics(text)

            if not self.did_something:
                if self.check_for_wake_phrase(text):
                    text = self.remove_wake_phrase(text)
                    if len(text) < 1:
                        msg = "What do you want?"
                        self.speak(msg)
                        text = self.listen().lower()
                        self.check_basics(text)
                    if not self.did_something:
                        if text != "":
                            if text[-1] in self.dict_of_main_strings['FORBIDDEN_SIGNS']:
                                text = text[:(len(text) - 1)]

                        self.speak("thinking about it")
                        self.client.send_message(text)
                        answer = self.client.receive_message()
                        if answer[:3] == "AT+":
                            answer = answer[3:]
                            threading.Thread(target=self.start_alarm, args=[answer]).start()
                            self.speak("Alarm set!")
                            self.last_said_text = "Alarm set!"
                        elif answer in self.dict_of_main_strings['EXIT_MESSAGES']:
                            self.speak(answer)
                            return "STOP"
                        else:
                            self.speak(answer)
                            self.last_said_text = answer


def main():
    """ This function creates the encryption object, the client and the main window. """
    encryption_object = module_from_file("encryption_object", "/home/pi/Desktop/yb_project_smart_mirror/encryption_object.py")
    encrypter = encryption_object.enc_dec()
    try:
        client = client_class(encrypter)
        client.create_client_and_connect()
        
        app = QApplication(sys.argv)
        alex_main_window(client)

        sys.exit(app.exec_())

    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    main()
