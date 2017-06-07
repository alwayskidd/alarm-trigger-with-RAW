import packet,event,device
# from event import Event
# from packet import Packet
# from device import Device
class  AP(device.Device): # has no  downlink traffic there
	def __init__(self,locations,CWmin,CWmax,timer,channel):
		device.Device.__init__(self,locations,CWmin,CWmax,timer,channel)
		self.AID=0
		self.status="Listen" # AP status: listen or transmit
		self.STA_list=[]

	def register_associated_STAs(self,STA_list):
		self.STA_list=STA_list

	def packet_received(self,received_packet):
	# This function is called when AP receives an packet from some STAs
	# Input:
	#	packet--the received packet at AP
		if self in received_packet.destination:
			if received_packet.packet_type=="RTS":
				self.packet_to_send=packet.Packet(self.timer,"CTS",self,[received_packet.source])
			if received_packet.packet_type=="Data":
				self.packet_to_send=packet.Packet(self.timer,"ACK",self,[received_packet.source])
			new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
			new_event.register_device(self)
			self.timer.register_event(new_event)
			self.IFS_expire_event=new_event
		self.packet_can_receive=None

	def IFS_expire(self):
	# This function is called AP has wait for an IFS, (most likely the SIFS)
	# The pending packet will be send
		if self.packet_to_send!=None: #may be the EIFS expired
			self.transmit_packet(self.packet_to_send)
			self.packet_to_send=None
		self.IFS_expire_event=None

	def transmission_end(self):
	# This function is called when AP finished its transmission
		assert self.packet_in_air, self.packet_in_air
		self.channel.clear_transmission_in_air(self.packet_in_air)
		print("packet from AP to STA "+str(self.packet_in_air.destination[0].AID)+" has been transmitted")
		self.packet_in_air=None
		self.status="Listen"
		return 0