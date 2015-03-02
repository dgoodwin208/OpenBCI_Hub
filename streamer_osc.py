
# requires pyosc
from OSC import OSCClient, OSCMessage

# Use OSC protocol to broadcast data (UDP layer), using "/openbci" stream. (NB. does not check numbers of channel as TCP server)



class OSCServer(object):

  def __init__(self, ip, port,address="/openbci"):
    self.ip = ip
    self.port = port
    self.address = address
	if len(args) > 0:
		self.ip = args[0]
	if len(args) > 1:
		self.port = args[1]
	if len(args) > 2:
		self.address = args[2]
	# init network
	print "Selecting OSC streaming. IP: ", self.ip, ", port: ", self.port, ", address: ", self.address
	self.client = OSCClient()
	self.client.connect( (self.ip, self.port) )	
		
	

  def handle_sample(self, sample):
    mes = OSCMessage(self.address)
	mes.append(sample.channel_data)
	# silently pass if connection drops
	try:
		self.client.send(mes)
	except:
		return	

		


	   