from flask import Flask
from flask import render_template
from flask import request
from flask import session

from flask.ext.socketio import SocketIO, send, emit

import open_bci_v3 as bci
import os
import time
import threading

from udp_server import UDPServer
from oscserver import OSCServer

#global variables:
#bciboard -> the link to the openbci board over UART
#bciboard_thread -> the secondary thread that runs the board
#bciboard_stopsignal -> Set True if the board should be stopped next second
#sock_server -> udp_ser
#latest_string -> Temporary string to pass data

HOST_IP = "0.0.0.0"
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

OUTPUT_OPTIONS = {"csv":False, "udp":False,"osc":True}

STREAM_TIMEOUTLAPSE = 10 #In seconds

def printData(sample):
  #Sample callback that can be passed into the openbci board
  global latest_string
  #print "Called!"
  #os.system('clear')
  output = ""
  output += "----------------"
  output += ("%f" %(sample.id))
  output += str(sample.channel_data)
  output += str(sample.aux_data)
  output += "----------------"
  print output
  latest_string = output

def boardDoContinueCallback():
  #The openbci board periodically checks to see if it should shut off
  global bciboard_stopsignal
  if bciboard_stopsignal:
    bciboard_stopsignal = False
    return False
  else:
    return True

def boardErrorCallback():
  #The openbci board periodically checks to see if it should shut off
  print "Sees that the board exited."

@app.route("/")
def hello():
  global bciboard
  try:
    output = "From board: " + latest_string + "And is streaming: " + str(bciboard.streaming)
  except Exception as e:
    print e
    output = "ERROR"
  return render_template('index.html',status = output)

@app.route("/board/", methods=["POST","GET"])
def board_general():
  global bciboard
  return "Nothing here yet"

@app.route("/board/channel/<channel_num>/<command>", methods=["POST","GET"])
def board_command_handler(channel_num,command):
  global bciboard
  if command == "on":
    return "turning channel " + str(channel_num) + "on "
  elif command == "off":
    return "turning channel " + str(channel_num) + "off"

#Filters, Streaming, 
@app.route("/board/<field>/<command>", methods=["POST","GET"])
def startstop_handler(field,command):
  global bciboard
  if field=="stream":
    print "Yes sees this"
    try:
      if command == "start":
        return set_boardstreaming(True)
      else:
        return set_boardstreaming(False)
    
    except Exception as e:
      print e
      return e
  elif field == "filter":
    try:
      if command == "start":
        return bciboard.enable_filters()
      else:
        return bciboard.disable_filters()
    except Exception as e:
      print e
      return e
  elif field == "connection":
    return (bciboard is not None)

def sendSocketMessage(sample):
  try:
    socketio.emit('stream', {'data': sample.channel_data,'t':sample.t}, namespace='/test')
  except Exception as e:
    print e

# @socketio.on('test event', namespace='/test')
# def test_message(message):
#   print 'test recieved'

@socketio.on('connect', namespace='/chat')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/chat')
def test_disconnect():
    print('Client disconnected')


def set_boardstreaming(doStart):
  global latest_string, bciboard,bciboard_thread,bciboard_stopsignal
  global sock_server, osc_server

  output = ""

  if doStart and not bciboard.streaming:
    #initialize the thread 
    #,sendSocketMessage
    bciboard_thread = threading.Thread(target=bciboard.start_streaming, args=[[printData,sock_server.handle_sample,osc_server.handle_sample,sendSocketMessage],boardDoContinueCallback,boardErrorCallback,STREAM_TIMEOUTLAPSE])
    #set daemon to true so the app.py can still be ended with a single ^C
    bciboard_thread.daemon = True
    #spawn the thread
    bciboard_thread.start() 
    output = "STARTING STREAMING"
    
  elif not doStart:

    bciboard_stopsignal = True
    #bciboard_thread = None
    output = "STOPPING STREAMING"
  else:
    output = "DID NOTHING: Likely trying to start while aleady streaming"

  return output

# @app.route("/change",method=["GET"])
# def getChange():
#     return "From board: " + latest_string


if __name__ == '__main__':
  # global latest_string, bciboard, bciboard_stopsignal
  # global sock_server, osc_server

  # bciboard_stopsignal = False
  # port = '/dev/ttyUSB0'
  # baud = 115200
  # bciboard = bci.OpenBCIBoard(port=port, is_simulator=True)
  # latest_string = "none yet"

  # args = {
  #   "host": HOST_IP,
  #   "port": '8888',
  #   "json": True,
  #   }
  # print args
  
  # sock_server = UDPServer(args["host"], int(args["port"]), args["json"])
  # osc_server = OSCServer(args["host"], 12345)
  # set_boardstreaming(True)

  # #Run the http server
  # app.run(host= HOST_IP)
  # socketio.run(app)


# =======
  global latest_string, bciboard, bciboard_stopsignal
  global sock_server, osc_server
  
  bciboard_stopsignal = False
  
  baud = 115200

  available_ports = bci.serial_ports()
  print "Sees the following port options: " + str(available_ports)
  print "It is currently strongly advised to specify the port in code"
  
  port = available_ports[1]
  bciboard = bci.OpenBCIBoard(port=port, is_simulator=False) 
  latest_string = "none yet"
  
  args = {
    "host": HOST_IP,
    "port": '8888',
    "json":True,
    }
  print args  
    
  sock_server = UDPServer(args["host"], int(args["port"]), args["json"])
  osc_server = OSCServer(args["host"], 12345)

  #set_boardstreaming(True)
  #Run the http server
  #app.run(host= HOST_IP)
  socketio.run(app)
  print "HERE"
  
