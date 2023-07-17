from flask import Flask, request, redirect, render_template
from user_agents import parse
import netifaces
import csv
import os
import time

app = Flask(__name__)
csv_file = 'userData.csv'

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

def save_user_data(mac_address, user_agent_info):
    if not os.path.isfile(csv_file):
        with open(csv_file, 'w') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(['Mac Address', 'Browser', 'Browser Version', 'Operating System', 'OS Version', 'Device Family', 'Device Brand', 'Device Model'])
    with open(csv_file, 'a') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow([mac_address] + user_agent_info)


@app.route('/')
def index():
    time.sleep(3)  # Simulate loading for 3 seconds
    connected_interface = get_connected_interface()
    mac_address = get_mac_address(connected_interface)

    if not os.path.isfile(csv_file):
        save_user_data(mac_address, [])
        return redirect('/page2')

    if not check_mac_address(mac_address):
        return redirect('/page2')

    return redirect('/page1')

@app.route('/page1')
def page1():
    return render_template('page1.html')

@app.route('/page2')
def page2():
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

    save_user_data(mac_address, user_agent_info)

    return render_template('page2.html', user_agent=user_agent)


if __name__ == '__main__':
    app.run(debug=True)
