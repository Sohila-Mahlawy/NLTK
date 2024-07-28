import re

import speech_recognition as sr
import pyttsx3
from playsound import playsound
import openai
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import time
# import pygame
from datetime import datetime
import threading



app = Flask(__name__)
app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Initialize the recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')

engine.setProperty('voice', voices[1].id)
api_key = "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"
openai.api_key = api_key

with app.app_context():
    class User( db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        email = db.Column(db.String(100))
        country=db.Column(db.String(100))


    class Alarm(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        time=db.Column(db.String(100))

        name = db.Column(db.String(1000))
        notes = db.Column(db.String(1000))


    db.create_all()

def parse_spoken_time(spoken_time):
    # Handle specific times like "3:00 p.m." or "4:00 a.m."
    specific_time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)?'
    # Handle phrases like "10 and 10 minutes" or "3 p.m. and half"
    phrase_time_pattern = r'(\d{1,2})\s*(AM|PM)?\s*and\s*(half|quarter|\d{1,2})\s*minutes?'

    match_specific = re.search(specific_time_pattern, spoken_time, re.IGNORECASE)
    match_phrase = re.search(phrase_time_pattern, spoken_time, re.IGNORECASE)

    hour, minutes, period = 0, 0, None

    if match_specific:
        hour, minutes, period = map(lambda x: x if x is not None else 0, match_specific.groups())
        hour, minutes = int(hour), int(minutes)
    elif match_phrase:
        hour, period, extra = match_phrase.groups()[:3]
        hour = int(hour)
        if extra.isdigit():
            minutes += int(extra)  # Add numerical minutes
        elif 'half' in extra.lower():
            minutes += 30  # Add 30 minutes for "half"
        elif 'quarter' in extra.lower():
            minutes += 15  # Add 15 minutes for "quarter"

    # Convert hour to 24-hour format based on period (AM/PM)
    if period and 'PM' in period.upper() and hour < 12:
        hour += 12
    elif period and 'AM' in period.upper() and hour == 12:
        hour = 0

    if 0 <= hour < 24 and 0 <= minutes < 60:
        return f"{hour:02d}:{minutes:02d}"
    else:
        return "Invalid time format"

def check_alarms():

        now = datetime.now().strftime("%H:%M")  # Get current time as a string
        with app.app_context():
         alarms = Alarm.query.filter_by(time=now).all()  # Query for any alarms matching the current time
        if alarms:

            for alarm in alarms:
                play_sound("alarm.wav")  # Your function to play a sound
                speak(alarm.notes)  # Your function to speak the notes




def play_sound(file_path):
    playsound(file_path)
def send_email(subject, message, to_email):
    # Email settings
    from_email = "support@argon-online.com"
    password = "Daleel@123"
    smtp_server = "smtp.office365.com"
    smtp_port = 587 # or 465 for SSL

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # Create server object with SSL option
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Secure the connection

    try:
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        speak("Email sent successfully!")
    except Exception as e:
        speak(f"Failed to send email: {e}")
    finally:
        server.quit()
def get_command_text():
    with sr.Microphone() as source:
        audio = recognizer.listen(source, timeout=None)  # Listen for a command
        try:
            command = recognizer.recognize_google(audio).lower()
            return jarvis(command)  # Return the recognized text
        except sr.UnknownValueError:
            return listen_for_wake_word()
        except sr.RequestError:
            speak("Sorry, I'm having trouble connecting.")
            return listen_for_wake_word()

def listen_for_wake_word():
    with sr.Microphone() as source:
          # Continuous listening
            print("Listening for 'Hey Jarvis'...")
            audio = recognizer.listen(source, timeout=None)  # Listen continuously
            try:
                text = recognizer.recognize_google(audio).lower()
                if "hey" in text:  # Wake word detected
                    speak("I'm listening...")
                    return get_command_text()  # Call the function to handle commands
            except sr.UnknownValueError:
                # Handle unrecognized speech, you might want to print something here
                pass
            except sr.RequestError:
                # Handle API request errors
                speak("Sorry, I'm having trouble connecting.")

def listen():
    # Use the microphone as source for input
    with sr.Microphone() as source:
        speak("Listening...")

        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print("You said: " + text)
            return text
        except sr.UnknownValueError:
            speak("Sorry, I did not understand that.")
            return None
def speak(text):
    engine.say(text)
    engine.runAndWait()
def set_timer(minutes):
    speak(f"Setting a timer for {minutes} minutes.")
    # Convert minutes to seconds
    seconds = minutes * 60

    # Use threading to wait for the timer without blocking the entire script
    timer_thread = threading.Thread(target=start_timer, args=(seconds,))
    timer_thread.start()

def start_timer(seconds):
    time.sleep(seconds)
    play_sound("2.wav")  # Replace with the path to your alarm sound
    speak("Time's up!")
def jarvis(text):



        if text:
            if "good morning" in text.lower():
                play_sound('1.mp3')
            elif "set timer" in text.lower():
                try:
                    # Extract the number of minutes from the command
                    minutes = int(re.findall(r'\d+', text)[0])
                    set_timer(minutes)
                except (IndexError, ValueError):
                    speak("I couldn't understand the number of minutes.")
            elif "send an email"in text.lower():
                speak("ok , sir, to whom you want to  send this mail  please write down the email ")
                sender = input("please write the email")
                if sender:
                    speak("ok got it , what is the subject ")
                    subject=listen()
                    speak("great ,what you want me to write  ")
                    message=listen()
                    send_email(subject,message,sender)
                    with app.app_context():
                         user=User.query.filter_by(email=sender).first()
                    if user:
                         speak("done ,  i have been sent it !")
                    else:
                        speak("seems for me that this  email is not in your contacts do you want me to add it ? ")
                        ans=listen()
                        if ans=="yes".lower():
                            speak("ok lets do it give him a name ")
                            name=listen()

                            with app.app_context():
                                new_user=User(name=name,email=sender)
                                db.session.add(new_user)
                                db.session.commit()
                            speak("done i have added it to your contacts ")
            elif "set an alarm" in text.lower():
              speak("ok ,when you want me to inform you ")
              time=listen()
              if time:
                  formatted_time = parse_spoken_time(time)

                  speak(f"done alarm set at{formatted_time} if there is any notes or somthing you want me to say it tell me ")
                  notes=listen()
                  with app.app_context():
                      new_alarm=Alarm(time=formatted_time,notes=notes)
                      db.session.add(new_alarm)
                      db.session.commit()
                  speak("ok sir ")
            elif "scare me" in text.lower():
                playsound("2.wav")








            elif "goodbye" in text.lower():
                speak("Goodbye!,sir i am always at your service ")

            # Add more commands and responses as needed
            else:
                response = openai.Completion.create(
                    engine="text-davinci-002",  # Choose the engine (e.g., text-davinci-002)
                    prompt=text,
                    max_tokens=50,  # Adjust max tokens based on desired response length
                    n=1  # Number of responses to generate
                )

                # Extract the generated answer from the response
                answer = response.choices[0].text.strip()

                # Print the answer
                speak(answer)

if __name__ == "__main__":
    while 1:
        listen_for_wake_word()
        check_alarms()