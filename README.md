# OpenBCI_Hub
A simple, web-based interface for connecting with the OpenBCI hardware and interfacing with software systems of your choice.

##Overview
OpenBCI Hub is a python (2.7) script that communicates over USB to the OpenBCI v3 board, and creates a Flask-based web server that allows for control and data access directly through a RESTful interface and web sockets, respectively. The output streaming methods supported are:
* OSC
* UDP
* Socket 
* (CSV coming soon)

##Installation
It is recommended to create a python virtual environment. Full details on virtualenvs can be found [here](http://docs.python-guide.org/en/latest/dev/virtualenvs/). You need pip for this to work, which can be installed easiest through either homebrew or easy_install
You can set up a venv anywhere, but for this example we set it up in the directory adjacent to the repo's root directory

```
> virtualenv ../venv #setup a virtual env (might need to specify 2.7 soon)
> source ../venv/bin/activate #start the virtual machine
> pip install -r requirements.txt #installs all the necesssary python libraries, takes a few minutes
```
##Running the Hub
Once the venv is running (second line in above codeblock), starting the server should be as easy as:
```
> python app.py
```
To get a grasp on things, it's probably easiest to start with a simulated board:
```
> python app.py --simulator
```
Then navigate your browser to your [localhost:5000](http://localhost:5000)

## RESTful API

The web-control interface has a few HTTP endpoints. 

When `app.py` is first started, the streaming is not started. You can start by sending a GET request to 
```
/board/stream/<start|stop>
```
so starting data out of the board is:
```
/board/stream/start
```

All streaming methods are by default turned on. To modify this you send GET requests to 

```
/output/<udp|csv|socket|osc>/<on|off|read>
```
so to turn off the udp streaming:
```
/output/udp/off
```

##Notes on this early version
This system is new and will be developed as rapidly as possible in the next few weeks by Dan Goodwin and Mel Van Londen. For now, a few architectual compromises have been made

* Switching between the simulator and live data requries a reset of the server (ctrl+C)
* Stopping the server before stopping the stream from a live device can crash your computer.
* Removing a device while it's streaming can crash your computer




