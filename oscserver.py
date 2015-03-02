
# requires pyosc
from OSC import OSCClient, OSCMessage

class OSCServer(object):

	def __init__(self, ip, port,address="/openbci"):
		self.ip = ip
		self.port = port
		self.address = address
		
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
