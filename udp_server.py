"""A server that handles a connection with an OpenBCI board and serves that
data over both a UDP socket server and a WebSocket server.

Requires:
  - pyserial
  - asyncio
  - websockets
"""

import argparse
import cPickle as pickle
import json
import open_bci_v3 as open_bci
import socket





class UDPServer(object):

  def __init__(self, ip, port, json):
    self.ip = ip
    self.port = port
    self.json = json
    self.server = socket.socket(
        socket.AF_INET, # Internet
        socket.SOCK_DGRAM)

  def send_data(self, data):
    self.server.sendto(data, (self.ip, self.port))

  def handle_sample(self, sample):
    if self.json:
      # Just send channel data.
      self.send_data(json.dumps(sample.channel_data))
    else:
      # Pack up and send the whole OpenBCISample object.
      self.send_data(pickle.dumps(sample))



if __name__ == "__main__":


  args = {
    "host":'0.0.0.0',
    "port": '8888',
    "json":"store_true",
  }
  
  sock_server = UDPServer(args["host"], int(args["port"]), args["json"])
  obci.start_streaming(sock_server.handle_sample)
