import sys, time
import requests
import json
import re

from bs4 import BeautifulSoup
from getpass import getpass
from requests_ntlm import HttpNtlmAuth
# from requests_kerberos import HTTPKerberosAuth

settings = json.load(open('settings.json'))

url = settings['server_address']
domain = settings['credentials']['domain']
session = None

def get_session(manual_input=False):
    global session
    uname = None
    passwd = None
    if not session:
        if manual_input:
            uname = raw_input("Enter your Kerberos username: ")
            passwd = getpass("Enter your password: ")
            print "--------------------------------"
        else:
            uname = str(settings['credentials']['username'])
            passwd = str(settings['credentials']['password'])

        session = requests.Session()
        session.auth = HttpNtlmAuth(domain + uname, passwd, session)

    return session  # store this somehow?

def get_usage_summary_table():
    session = get_session()
    r = requests.get(url, auth=session.auth)
    if r.status_code == 200:
        c = r.content
        soup = BeautifulSoup(c)
        # Get the table
        usage_summary_table = soup.body.findAll('table', attrs={'class':'ms-rteTable-1'})[0]
        return usage_summary_table
    else: 
        print "Connection error"
        print "Error Code: ", r.status_code
        print r.content
        sys.exit(0)

def get_usage_details_table():
    session = get_session()
    r = requests.get(url, auth=session.auth)
    if r.status_code == 200:
        c = r.content
        soup = BeautifulSoup(c)
        # Get the table
        usage_details_table = soup.body.findAll('table', attrs={'class':'ms-rteTable-1'})[1]
        return usage_details_table
    else: 
        print "Connection error"
        print "Error Code: ", r.status_code
        print r.content
        sys.exit(0)

def print_table_vertical(table):
    rows = []
    for row in table.findAll('tr'):
        rows.append(row.findAll('td'))
    rows = zip(*rows)

    for row in rows:
        ls = []
        for col in row:
            ls.append(col.text)
        print '{0:23}: {1}'.format(*ls)

def summary_table_to_json(table):
    if not table:
        table = get_usage_summary_table()
    rows = []
    for row in table.findAll('tr'):
        rows.append(row.findAll('td'))
    # rows = zip(*rows)

    header_row = rows[0]
    data_row = rows[1]
    for i in range(len(header_row)):
        header = header_row[i]
        header = header.text.strip().lower()
        header = re.sub(r'\s-\s', '-', header)
        header = re.sub(r'\s+', '_', header)
        header_row[i] = header

    data = dict()
    for c in range(len(data_row)):
        col = data_row[c]
        data[header_row[c]] = col.text

    formatted_data = dict()
    formatted_data["bandwidth_class"] = data["bandwidth_class"]
    formatted_data["policy_bytes"] = {"sent" : data["policy_bytes_sent"], "received": data["policy_bytes_received"]}
    formatted_data["actual_bytes"] = {"sent" : data["actual_bytes_sent"], "received": data["actual_bytes_received"]}
    
    return formatted_data

def details_table_to_json(table):
    if not table:
        table = get_usage_details_table()
    rows = []
    for row in table.findAll('tr'):
        rows.append(row.findAll('td'))

    header_row = rows[0]
    data_rows = rows[1:]
    for i in range(len(header_row)):
        header = header_row[i]
        header = header.text.strip().lower()
        header = re.sub(r'\s-\s', '-', header)
        header = re.sub(r'\s+', '_', header)
        header_row[i] = header

    data = []
    for r in range(len(data_rows)):
        device_data = dict()
        device_row = data_rows[r]
        for c in range(len(device_row)):
            col = device_row[c]
            device_data[header_row[c]] = col.text
        data.append(device_data)

    formatted_data = list()
    for device_data in data:
        formatted_device_data = dict()
        formatted_device_data["network_address"] = device_data["network_address"]
        formatted_device_data["host"] = device_data["host"]
        formatted_device_data["comment"] = device_data["comment"]
        formatted_device_data["policy_bytes"] = {"sent" : device_data["policy_bytes_sent"], "received": device_data["policy_bytes_received"]}
        formatted_device_data["actual_bytes"] = {"sent" : device_data["actual_bytes_sent"], "received": device_data["actual_bytes_received"]}
        formatted_data.append(formatted_device_data)

    return formatted_data

def get_json_all_data():
    session = get_session()
    r = requests.get(url, auth=session.auth)
    data = None
    if r.status_code == 200:
        c = r.content
        soup = BeautifulSoup(c)
        # Get the tables
        tables = soup.body.findAll('table', attrs={'class':'ms-rteTable-1'})
        usage_summary_table = tables[0]
        usage_details_table = tables[1]

        summary_json = summary_table_to_json(usage_summary_table)
        summary_json["devices"] = details_table_to_json(usage_details_table)
        
        data = {"status" : "OK", "message" : summary_json }
    else: 
        data = {"status" : "Error", "status_code" : r.status_code, 
            "message" : "A connection error occurred."}
    return json.dumps(data)

def main():
    for i in xrange(0, 5):
        data = json.loads(get_json_all_data())
        if data["status"] == "OK":
            data = data["message"]
            bandwidth_class = data["bandwidth_class"]
            actual_received = data["actual_bytes"]["received"]
            policy_received = data["policy_bytes"]["received"]
            print "Bandwidth Class: ", bandwidth_class
            print "Bytes Received: Policy: {0} ; Actual: {1}".format(policy_received, actual_received)
        time.sleep(10*60)
    

if __name__ == '__main__':
    main()

    print
    raw_input("Press ENTER to exit") # pause