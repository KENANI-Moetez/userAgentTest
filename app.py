from flask import Flask, request, redirect, render_template
from user_agents import parse
import netifaces
import csv
import os
from twilio.rest import Client
import random
import phonenumbers

app = Flask(__name__)

# Twilio API Credentials
account_sid = "AC1e90af84045176a38b2a849bd58448da"
auth_token = "66d27fbd66765f6f25a64d201dd474ae"
verified_number = "+17626752413"


userdata=[]
csv_file = 'userData.csv'
otp_data = {}


def get_mac_address(interface):
    try:
        mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        return mac
    except KeyError:
        return None

def get_connected_interface():
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET]
    connected_interface = default_gateway[1]
    return connected_interface

def check_mac_address(mac_address):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
               if row[0] == mac_address:
                return True
        return False

def save_user_data(mac_address, user_agent_info, number):
    header = ['Mac Address', 'Browser', 'Browser Version', 'Operating System', 'OS Version', 'Device Family', 'Device Brand', 'Device Model', 'Phone Number']

    if not os.path.isfile(csv_file):
        with open(csv_file, 'w') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(header)
    with open(csv_file, 'a') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([mac_address] + user_agent_info + [number])

def is_user_data_saved(mac_address):
    with open(csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if row[0] == mac_address:
                return True
        return False

def generateOTP():
    return random.randint(100000, 999999)

def getOTPApi(number, otp):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=verified_number,
        to=number,
        body='Your OTP is ' + str(otp)
    )

    return True

def formatPhoneNumber(number):
    try:
        parsed_number = phonenumbers.parse(number, "TN")
        if phonenumbers.is_valid_number(parsed_number):
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted_number
    except phonenumbers.NumberParseException:
        pass
    return None
@app.route('/')
def index():
    connected_interface = get_connected_interface()
    mac_address = get_mac_address(connected_interface)

    if not check_mac_address(mac_address):
        return redirect('/login')

    return redirect('/page1')

@app.route('/page1')
def page1():
    return render_template('page1.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    connected_interface = get_connected_interface()
    mac_address = get_mac_address(connected_interface)

    if is_user_data_saved(mac_address):
        return render_template('login.html', user_agent=None)

    user_agent_string = request.headers.get('User-Agent')
    user_agent = parse(user_agent_string)

    user_agent_info = [
        user_agent.browser.family,
        user_agent.browser.version_string,
        user_agent.os.family,
        user_agent.os.version_string,
        user_agent.device.family,
        user_agent.device.brand,
        user_agent.device.model
    ]
    
    if request.method == 'POST':
        number = request.form['number']
        formatted_number = formatPhoneNumber(number)

        if formatted_number:
            otp = generateOTP()
            otp_data[formatted_number] = str(otp)
            otp_sent = getOTPApi(formatted_number, otp)
            if otp_sent:
                return render_template('enterOTP.html', number=formatted_number)

    return render_template('login.html', user_agent=user_agent)


@app.route('/getOTP', methods=['POST'])
def getOTP():
    number = request.form['number']
    formatted_number = formatPhoneNumber(number)
    if formatted_number:
        otp = generateOTP()
        otp_data[formatted_number] = str(otp)
        otp_sent = getOTPApi(formatted_number, otp)
        if otp_sent:
            return render_template('enterOTP.html', number=formatted_number)
    return "Failed to send OTP. Please try again."

@app.route('/verifyOTP', methods=['POST'])
def verifyOTP():
    entered_otp = request.form['otp'].strip()
    number = request.form['number']
    formatted_number = formatPhoneNumber(number)
    
    if formatted_number and formatted_number in otp_data:
        sent_otp = otp_data[formatted_number]
        if entered_otp == sent_otp:
            del otp_data[formatted_number]
            
            # Save user data after successful OTP verification
            connected_interface = get_connected_interface()
            mac_address = get_mac_address(connected_interface)
            user_agent_string = request.headers.get('User-Agent')
            user_agent = parse(user_agent_string)
            
            user_agent_info = [
                user_agent.browser.family,
                user_agent.browser.version_string,
                user_agent.os.family,
                user_agent.os.version_string,
                user_agent.device.family,
                user_agent.device.brand,
                user_agent.device.model
            ]
            
            save_user_data(mac_address, user_agent_info, formatted_number)
            
            return render_template('page1.html')
    
    error_message = "Incorrect OTP. Please try again."
    return render_template('enterOTP.html', number=formatted_number, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
