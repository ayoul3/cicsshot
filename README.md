# CICSshot
## Description  
CICSshot takes screenshots of CICS.

## Features    
* Get screenshots of CICS transactions
* Handles authenticated mode

## Usage
```
$python cicsshot.py -h

              
            ▄████▄      ██▓    ▄████▄       ██████      ██████  ██░ ██  ▒█████  ▄▄▄█████▓
           ▒██▀ ▀█     ▓██▒   ▒██▀ ▀█     ▒██    ▒    ▒██    ▒ ▓██░ ██▒▒██▒  ██▒▓  ██▒ ▓▒
           ▒▓█    ▄    ▒██▒   ▒▓█    ▄    ░ ▓██▄      ░ ▓██▄   ▒██▀▀██░▒██░  ██▒▒ ▓██░ ▒░    
           ▒▓▓▄ ▄██▒   ░██░   ▒▓▓▄ ▄██▒     ▒   ██▒     ▒   ██▒░▓█ ░██ ▒██   ██░░ ▓██▓ ░ 
           ▒ ▓███▀ ░   ░██░   ▒ ▓███▀ ░   ▒██████▒▒   ▒██████▒▒░▓█▒░██▓░ ████▓▒░  ▒██▒ ░ 
           ░ ░▒ ▒  ░   ░▓     ░ ░▒ ▒  ░   ▒ ▒▓▒ ▒ ░   ▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒░ ▒░▒░▒░   ▒ ░░   
             ░  ▒       ▒ ░     ░  ▒      ░ ░▒  ░ ░   ░ ░▒  ░ ░ ▒ ░▒░ ░  ░ ▒ ▒░     ░    
           ░            ▒ ░   ░           ░  ░  ░     ░  ░  ░   ░  ░░ ░░ ░ ░ ▒    ░      
           ░ ░          ░     ░ ░               ░           ░   ░  ░  ░    ░ ░           
           ░                  ░                                                          
                  
                            Screenshotting CICS transactions !		Author: @Ayoul3__

usage: cicsshot.py [-h] [-a APPLID] [-U USERID] [-P PASSWORD] IP PORT FILE

CicsScreen: a tool to screenshot transactions on CIS transaction servers on
z/OS

positional arguments:
  IP                    The z/OS Mainframe IP or Hostname
  PORT                  CICS/VTAM server Port
  FILE                  File containing a list of transactions

optional arguments:
  -h, --help            show this help message and exit
  -a APPLID, --applid APPLID
                        CICS ApplID on VTAM, default is CICS
  -U USERID             Username for CICS in case authentication is needed
  -P PASSWORD           Password in case authentication is needed

```
## Prerequisites
3270 Python library [py3270](https://pypi.python.org/pypi/py3270/0.2.0)
x3270, s3270 or wc3270.exe installed on your system

## Use case
```
root@kali:~/cics# python cicsshot.py -a CICS 192.168.1.201 23 list.txt
[+] Launching 5 threads connecting to 192.168.1.201:23, APPLID=CICS
[+] Launching 5 threads connecting to 192.168.1.201:23, APPLID=CICS
[+] Saving results to folder ./screens
[*] Got transaction ABRW
[*] Got transaction AADD
[*] Got transaction AMNU
[*] Got transaction AINQ
[*] Got transaction AORD
[*] Got transaction AUPD
```

## Copyright and license  
CICSshot is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.  
CICSshot is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with nmaptocsv. If not, see http://www.gnu.org/licenses/.

## Contact
Ayoub ELAASSAL ayoul3.zos at gmail dot com
