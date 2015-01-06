RHIT-BandwidthScraper
==========
Converts the Rose-Hulman Bandwidth website to JSON

#### Overview:  
I was getting tired of needing to relogin to the webpage on which students are able to check their bandwidth, and so I wrote this script to authenticate with the site and put all the relevant information into JSON.

#### Description:  
This project reads in the settings.json file which contains a user's credentials, uses those credentials to authenticate with the bandwidth webpage, and then scrapes the two tables and places them into nicely parseable JSON.  
The first table is the Network Usage Summary table. It contains the Bandwidth Class (restricted or not; if so, the effective cap download speed), as well as the bytes used up and down by the authenticated used. Policy Bytes are scaled with on-campus and off-hours usage. Actual Bytes are the unscaled version of Policy Bytes.  
The second table contains a list of devices the authenticated user has registered on the network and a breakdown of their individual network usage.

#### Further Steps:
The initial thought for this project was a method of a RESTful API for my Raspberry Pi. I have not decided how I want to set that up yet. I think I would need to securely send user credentials to the API, so I need to figure out how to do that first.  

I want to further extend this code by creating a live graph of the bandwidth usage for a user by polling this data every few minutes. I have some ideas how to manage this, so I will start this next.

Running the program
===================
1. Make sure Python 2.7 is installed
2. Update the settings.json file with your Rose-Hulman network credentials, then run from a command-line
    ```
    python scraper.py
    ```


Default Settings (settings.json)
============
Please remember to change the username and password fields, otherwise this script won't work.
```javascript
{
    "server_address": "https://netreg.rose-hulman.edu/tools/networkUsage.pl",
    "credentials": {
        "domain": "ROSE-HULMAN\\",
        "username": "USERNAME",
        "password": "PASSWORD"
    }
}
```

Sample Output
=============
```javascript
{
    "status": "OK",
    "message": {
        "bandwidth_class": "Unrestricted",
        "policy_bytes": {
            "received": "718.59 MB",
            "sent": "114.25 MB"
        },
        "devices": [
            {
                "comment": "laptop wireless",
                "host": "",
                "network_address": "00:24:XX:XX:XX:XX",
                "policy_bytes": {
                    "received": "570.24 MB",
                    "sent": "102.16 MB"
                },
                "actual_bytes": {
                    "received": "947.18 MB",
                    "sent": "150.15 MB"
                }
            },
            {
                "comment": "Created by Captive Portal service",
                "host": "",
                "network_address": "B0:79:XX:XX:XX:XX",
                "policy_bytes": {
                    "received": "37.83 MB",
                    "sent": "2.64 MB"
                },
                "actual_bytes": {
                    "received": "125.38 MB",
                    "sent": "5.23 MB"
                }
            },
            {
                "comment": "laptop",
                "host": "",
                "network_address": "F0:DE:XX:XX:XX:XX",
                "policy_bytes": {
                    "received": "118.76 MB",
                    "sent": "12.11 MB"
                },
                "actual_bytes": {
                    "received": "191.42 MB",
                    "sent": "19.13 MB"
                }
            }
        ],
        "actual_bytes": {
            "received": "1,246.71 MB",
            "sent": "171.15 MB"
        }
    }
}
```
