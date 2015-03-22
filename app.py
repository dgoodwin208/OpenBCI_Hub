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
import argparse

#global variables:
#bciboard -> the link to the openbci board over UART
#bciboard_thread -> the secondary thread that runs the board
#bciboard_stopsignal -> Set True if the board should be stopped next second
#sock_server -> udp_ser
#latest_string -> Temporary string to pass data
#bciboard_callbacks -> array of all call back functions
#docallback_osc -> boolean to stream over osc
#docallback_udp -> boolean to stream over udp
#docallback_socket -> boolean to stream over socket (works with hub)
#docallback_csv -> to csv (not currently implement)
#docallback_toconsole -> print to python log?

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

def modify_bcicallbacks(string_command,do_set):
  global bciboard_callbacks
  global docallback_toconsole, docallback_csv,docallback_socket,docallback_osc, docallback_udp

  if string_command =="udp":
    docallback_udp = do_set
  elif string_command == "csv":
    docallback_csv = do_set
  elif string_command == "socket":
    docallback_socket = do_set
  elif string_command == "osc":
    docallback_osc = do_set
  elif string_command == "console":
    docallback_toconsole = do_set
  else:
    #We don't know this input
    return None
  cbacks = []
  if docallback_osc:
    cbacks.append(osc_server.handle_sample)
  if docallback_udp:
    cbacks.append(sock_server.handle_sample)
  if docallback_udp:
    cbacks.append(sendSocketMessage)
  if docallback_toconsole:
    cbacks.append(printData)
  #TODO: finish the CSV streaming option

  #write to the global variable (used by the streaming loop)
  bciboard_callbacks = cbacks

  return 1


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




#Filters, etc. are handled in this block
@app.route("/board/<field>/<command>", methods=["POST","GET"])
def startstop_handler(field,command):
  global bciboard
  if field=="stream":

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

@app.route("/output/<streamtype>/<onoffread>", methods=["POST","GET"])
def streamoutput_handler(streamtype,onoffread):
  try:
    if onoffread=="read":
      output = ""
      if streamtype =="udp":
        output += str(docallback_udp)
      elif streamtype == "csv":
        output += str(docallback_csv)
      elif streamtype == "socket":
        output += str(docallback_socket)
      elif streamtype == "osc":
        output += str(docallback_osc)
      elif streamtype == "console":
        output += docallback_toconsole 
      return output 

    res = modify_bcicallbacks(streamtype,onoffread=="on")

    if not res:
      return "ERROR: STREAMTYPE NOT CORRECT."
    else:
      return "SUCCESS"
  except Exception as e:
      print e
      return e

def sendSocketMessage(sample):
  try:
    socketio.emit('stream', {'data': sample.channel_data,'t':sample.t}, namespace='/test')
  except Exception as e:
    print e

# @socketio.on('test event', namespace='/test')
# def test_message(message):
#   print 'test recieved'

@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


def set_boardstreaming(doStart):
  global latest_string, bciboard,bciboard_thread,bciboard_stopsignal
  
  output = ""

  if doStart and not bciboard.streaming:
    #initialize the thread 
    #,sendSocketMessage
    
    
    bciboard_thread = threading.Thread(target=bciboard.start_streaming, args=[bciboard_callbacks,boardDoContinueCallback,boardErrorCallback,STREAM_TIMEOUTLAPSE])
    
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


if __name__ == '__main__':

  global latest_string, bciboard, bciboard_stopsignal
  global sock_server, osc_server
  global bciboard_callbacks
  global docallback_toconsole, docallback_csv,docallback_socket,docallback_osc, docallback_udp


  parser = argparse.ArgumentParser(description="OpenBCI 'user'")
  parser.add_argument('-sim', '--simulator', action='store_true',
        help="Run the openbci simulator, rather than real data")
  
  parser.add_argument('-p', '--port',
        help="Port to connect to OpenBCI Dongle " +
        "( ex /dev/ttyUSB0 or /dev/tty.usbserial-* )")

  args = parser.parse_args()

  #initialize the stop signal for the repeate streaming data
  bciboard_stopsignal = False
  
  available_ports = bci.serial_ports()
  print "Sees the following port options: " + str(available_ports)
  print "It is currently strongly advised to specify the port in code"
  
  #port = available_ports[1]
  if args.port:
    print "Using manually specific port: " + str(args.port)
    specific_port = args.port
  else:
    specific_port = None

  use_sim= False
  if args.simulator:
    print "Initializing the simulator board"
    use_sim = True
  bciboard = bci.OpenBCIBoard(is_simulator=use_sim, port=specific_port)  
  latest_string = "none yet"
  
  args = {
    "host": HOST_IP,
    "port": '8888',
    "json": True,
    }
  print args  
  
  sock_server = UDPServer(args["host"], int(args["port"]), args["json"])
  osc_server = OSCServer(args["host"], 12345)

  #define the list of callback fundctions now:
  docallback_toconsole = True
  docallback_csv = False
  docallback_socket = True
  docallback_osc = True
  docallback_udp = True
  bciboard_callbacks = [sock_server.handle_sample,osc_server.handle_sample,sendSocketMessage,printData] 

  socketio.run(app)
  print "HERE"
  
