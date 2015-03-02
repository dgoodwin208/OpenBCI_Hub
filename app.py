from flask import Flask
from flask import render_template

import open_bci_v3 as bci
import os
import threading
from udp_server import UDPServer


#global variables:
#bciboard -> the link to the openbci board over UART
#bciboard_thread -> the secondary thread that runs the board
#bciboard_stopsignal -> Set True if the board should be stopped next second
#sock_server -> udp_ser
#latest_string -> Temporary string to pass data
def printData(sample):
	global latest_string
	#print "Called!"
	#os.system('clear')
	output = ""
	output += "----------------"
	output += ("%f" %(sample.id))
	output += str(sample.channel_data)
	output += str(sample.aux_data)
	output += "----------------"

	latest_string = output

def boardDoContinueCallback():
	global bciboard_stopsignal
	print "boardDoContinueCallback"
	if bciboard_stopsignal:
		bciboard_stopsignal = True
		return False
	else:
		return True
app = Flask(__name__)

@app.route("/")
def hello():
	global bciboard
	try:
		output = "From board: " + latest_string + "And is streaming: " + str(bciboard.streaming)
	except Exception as e:
		print e
		output = "ERROR"
	return render_template('index.html',status = output)

@app.route("/startstop")
def postChange():
	global latest_string, bciboard,bciboard_thread
	global bciboard_stopsignal, sock_server
	print "Entered startstop"
	try:
		if not bciboard.streaming:
			#initialize the thread
			bciboard_thread = threading.Thread(target=bciboard.start_streaming, args=[[printData,sock_server.handle_sample],boardDoContinueCallback])
			#set daemon to true so the app.py can still be ended with a single ^C
			bciboard_thread.daemon = True
			#spawn the thread
			bciboard_thread.start()	
			output = "STARTING STREAMING"
		else:
			bciboard_stopsignal = True
			#bciboard_thread = None
			output = "STOPPING STREAMING"
		
	except Exception as e:
		print e 

	return output
# @app.route("/change",method=["GET"])
# def getChange():
#     return "From board: " + latest_string

if __name__ == '__main__':
	global latest_string, bciboard, bciboard_stopsignal,sock_server
	
	bciboard_stopsignal = False
	port = '/dev/ttyUSB0'
	baud = 115200
	bciboard = bci.OpenBCIBoard(port=port, is_simulator=True)
	latest_string = "none yet"
	
	args = {
    "host":'192.168.3.53',
    "port": '8888',
    "json":True,
  	}
	print args  
  	sock_server = UDPServer(args["host"], int(args["port"]), args["json"])
 
	postChange()
 	#Run the http server
	app.run(host= '0.0.0.0')
	
	