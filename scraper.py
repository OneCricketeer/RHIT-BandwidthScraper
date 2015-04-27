import sys, time, os
import requests
import json
import re

from bs4 import BeautifulSoup
from getpass import getpass
from requests_ntlm import HttpNtlmAuth
from db_models import DbUsage, DbBandwidth, DbBandwidthDevice, DbBandwidthDeviceUsage
# from requests_kerberos import HTTPKerberosAuth

__location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
settings_file = os.path.join(__location__, 'settings.json')
settings = json.load(open(settings_file, 'r'))

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
        usage_summary_table = soup.body.findAll('table', attrs={'class': 'ms-rteTable-1'})[0]
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
        usage_details_table = soup.body.findAll('table', attrs={'class': 'ms-rteTable-1'})[1]
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
    formatted_data["policy_bytes"] = {"sent": data["policy_bytes_sent"], "received": data["policy_bytes_received"]}
    formatted_data["actual_bytes"] = {"sent": data["actual_bytes_sent"], "received": data["actual_bytes_received"]}

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
    mac_addr_separator = ':'
    mask_amt = 2
    for device_data in data:
        formatted_device_data = dict()
        split_mac = device_data["network_address"].split(mac_addr_separator)
        mac_addr = ('XX' + mac_addr_separator) * mask_amt + mac_addr_separator.join(split_mac[mask_amt:])
        formatted_device_data["network_address"] = mac_addr
        formatted_device_data["host"] = device_data["host"]
        formatted_device_data["comment"] = device_data["comment"]
        formatted_device_data["policy_bytes"] = {"sent": device_data["policy_bytes_sent"],
                                                 "received": device_data["policy_bytes_received"]}
        formatted_device_data["actual_bytes"] = {"sent": device_data["actual_bytes_sent"],
                                                 "received": device_data["actual_bytes_received"]}
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
        tables = soup.body.findAll('table', attrs={'class': 'ms-rteTable-1'})
        usage_summary_table = tables[0]
        usage_details_table = tables[1]

        summary_json = summary_table_to_json(usage_summary_table)
        summary_json["devices"] = details_table_to_json(usage_details_table)

        data = {"status": "OK", "message": summary_json}
    else:
        data = {"status": "Error", "status_code": r.status_code,
                "message": "A connection error occurred.", "content": r.content}
    return json.dumps(data)


def db_save(data):
    from db_models import Session

    db_session = Session()

    # parse it
    actual_received = data["actual_bytes"]["received"]
    policy_received = data["policy_bytes"]["received"]
    actual_sent = data["actual_bytes"]["sent"]
    policy_sent = data["policy_bytes"]["sent"]

    # total usage
    db_total_usage = DbUsage(
        policy_received=float(re.sub(r'[^\d.]', '', policy_received)),
        actual_received=float(re.sub(r'[^\d.]', '', actual_received)),
        policy_sent=float(re.sub(r'[^\d.]', '', policy_sent)),
        actual_sent=float(re.sub(r'[^\d.]', '', actual_sent))
    )
    db_session.add(db_total_usage)
    db_session.commit()

    # current bandwidth cap
    db_bandwidth = DbBandwidth(bandwidth_class=data["bandwidth_class"], usage_id=db_total_usage.id)
    db_session.add(db_bandwidth)
    db_session.commit()

    # per device usage
    devices = data["devices"]
    for dev in devices:
        actual_received = dev["actual_bytes"]["received"]
        policy_received = dev["policy_bytes"]["received"]
        actual_sent = dev["actual_bytes"]["sent"]
        policy_sent = dev["policy_bytes"]["sent"]

        db_dev_usage = DbUsage(
            policy_received=float(re.sub(r'[^\d.]', '', policy_received)),
            actual_received=float(re.sub(r'[^\d.]', '', actual_received)),
            policy_sent=float(re.sub(r'[^\d.]', '', policy_sent)),
            actual_sent=float(re.sub(r'[^\d.]', '', actual_sent))
        )
        db_session.add(db_dev_usage)
        db_session.commit()

        # add or get device info
        db_bandwidth_device = DbBandwidthDevice(
            net_addr=dev["network_address"],
            host=dev["host"],
            comment=dev["comment"]
        )
        query = db_session.query(DbBandwidthDevice).filter(DbBandwidthDevice.net_addr == db_bandwidth_device.net_addr)
        if query.count() == 0:
            db_session.add(db_bandwidth_device)
            db_session.commit()
        else:
            db_bandwidth_device = query.first()
        db_bandwidth_dev_usage = DbBandwidthDeviceUsage(
            bandwidth_id=db_bandwidth.id,
            device_id=db_bandwidth_device.id,
            usage_id=db_dev_usage.id
        )
        db_session.add(db_bandwidth_dev_usage)
        db_session.commit()


def main():
    delay = 360

    while True:
        data = json.loads(get_json_all_data())
        if data["status"] == "OK":
            data = data["message"]
            bandwidth_class = data["bandwidth_class"]
            actual_received = data["actual_bytes"]["received"]
            policy_received = data["policy_bytes"]["received"]

            print "Bandwidth Class: ", bandwidth_class
            print "Bytes Received: Policy: {0} ; Actual: {1}".format(policy_received, actual_received)

            db_save(data)
        else:
            print data

        time.sleep(delay)


if __name__ == '__main__':
    main()

    print
    raw_input("Press ENTER to exit")  # pause