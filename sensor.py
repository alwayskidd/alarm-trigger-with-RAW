import event,device,packet,system_timer
import random,statistics_collection

class Sensor(device.Device):
	def __init__(self,AID,CWmin,CWmax,locations,RTS_enabled,suspend_enabled,AP,timer,channel):
		device.Device.__init__(self,locations,CWmin,CWmax,timer,channel)
		self.RTS_enabled,self.suspend_enabled=RTS_enabled,suspend_enabled # True or False
		# self.packet_to_send=None
		self.AID=AID
		self.AP=AP
		self.receiving_power=0 # mW
		self.number_of_attempts=0
		self.number_of_backoffs=0

	def generate_one_packet(self):
	#This function is called when the sensor is triggered by the event 
	#After being triggered this sensor generates an alarm report
		new_packet=packet.Packet(self.timer,"Data",self,[self.AP])
		assert self.status=="Sleep"
		self.status="Listen"
		self.queue.append(new_packet) # push this packet into the queue
		# statistics_collection.collector.register_packet_generated()
		if self.channel_state=="Idle": # wait for an DIFS before tranmission
			new_event=event.Event("IFS expire",self.timer.current_time+self.timer.DIFS)
			new_event.register_device(self)
			self.IFS_expire_event=new_event
			self.timer.register_event(new_event)
			self.packet_to_send=new_packet

	def back_off(self):
	#This function is called when a backoff time slot has passed
	#This sensor's backoff timer is count down in this function and transmission is triggered when timer<=0
	#Output:
	#	True--this sensor is still backing off
	#	False--this senosr is not backing off
		if (self.backoff_status=="Off" or not self.queue or self.status!="Listen"): # backoff timer will not decrease
			return False
		assert self.channel_state=="Idle", "channel is busy while back off is not turned off"
		self.backoff_timer-=1
		if self.backoff_timer<=0: # transmit this packet immediately
			if self.RTS_enabled: # generate an RTS frame to send to AP
				packet=packet.Packet(self.timer,"RTS",self,[self.AP])
				self.transmit_packet(packet)
			else: #send the pending data
				packet=self.queue[0]
				self.transmit_packet(packet)
			self.status="Transmit"
			self.packet_can_receive=None
			return False
		else:
			return True

	def transmission_end(self):
	#This function is called when this sensor finish a frame transmission
		# self.channel.clear_transmission_in_air(self.packet_in_air)
		if self.packet_in_air.packet_type=="RTS": # sensor need to wait a CTS timeout
			new_event=event.Event("reply timeout",self.timer.current_time+self.timer.SIFS+
				packet.Packet(self.timer,"CTS",self,[self.AP]).transmission_delay()+1)
		elif self.packet_in_air.packet_type=="Data": # sensor need to wait an ACK timeout
			new_event=event.Event("reply timeout",self.timer.current_time+self.timer.SIFS+
				packet.Packet(self.timer,"ACK",self,[self.AP]).transmission_delay()+1)
		self.channel.clear_transmission_in_air(self.packet_in_air)
		new_event.register_device(self)
		self.time_out_event=new_event
		self.timer.register_event(new_event)
		self.packet_in_air=None
		self.backoff_status="Off"
		self.status="Listen"

	def reply_timeout(self):
	#This function is called when this sensor failes receiving a reply from AP
	#In this simulation, this will only happens when there is a collision
		self.backoff_stage=min(self.backoff_stage*2,self.CWmax)
		self.backoff_timer=random.randint(0,self.backoff_stage-1)
		if self.channel_state=="Idle" and self.NAV_expire_event==None: 
		#channel is idle and no NAV need to be expired, wait for an DIFS to start backoff
			new_event=event.Event("IFS expire",self.timer.current_time+self.timer.DIFS)
			new_event.register_device(self)
			self.timer.register_event(new_event)
			self.IFS_expire_event=new_event
		self.time_out_event=None
		statistics_collection.collector.register_collision()

	def __NAV_renew__(self,packet):
	#This function is called when receiving a packet which is not target for itself
		NAV=packet.NAV
		if self.NAV_expire_event!=None: # remove the former NAV expire event from the timer
			self.timer.remove_event(self.NAV_expire_event)
			self.NAV_expire_event=None
		if NAV!=0: # register a new NAV event in the timer
			new_event=event.Event("NAV expire",self.timer.current_time+NAV+1)
			new_event.register_device(self)
			self.timer.register_event(new_event)
			self.NAV_expire_event=new_event
		else: # immediately expire the NAV
			self.NAV_expire()

	def NAV_expire(self):
	#This function is called when NAV has expired 
	#This sensor will start its backoff timer after a DIFS
		assert self.IFS_expire_event==None
		if self.channel_state=="Idle" and self.queue: # start backoff after a DIFS if queue is not 
		# empty and channel is idle
			new_event=event.Event("IFS expire",self.timer.current_time+self.timer.DIFS)
			new_event.register_device(self)
			self.timer.register_event(new_event)
			self.IFS_expire_event=new_event
		self.NAV_expire_event=None

	def IFS_expire(self):
	#This function is called when an IFS duration is expired and channel is Idle
	#After this IFS duration, the sensor will start transmission or start backoff timer
		if self.packet_to_send==None: #start backoff counter as no packet need to be sent
			self.backoff_status="On"
			if self.timer.backoff_status=="Off": # register a backoff event
				new_event=event.Event("backoff",self.timer.current_time+self.timer.slot_time)
				new_event.register_device(self)
				self.timer.register_event(new_event)
				self.timer.backoff_status="On"
				print("backoff is on")
		elif (self.channel_state=="Idle" or self.packet_to_send.packet_type=="ACK" or
		self.packet_to_send.packet_type=="CTS"): # start a transmission for the pending packet
			self.transmit_packet(self.packet_to_send)
			self.packet_to_send=None
		self.IFS_expire_event=None


	def packet_received(self,packet):
	#This function is called when a packet is finished tranmission in the air and can be 
	#received by this sensor
	#Input: 
	#	packet--the packet can be received by this sensor
		import time
		assert self.packet_can_receive==packet
		self.packet_can_receive=None
		if self.IFS_expire_event!=None: 
		#clear this event, this event may be register when channel becomes Idle, 
		#EIFS is registered in the update receiving power function
			self.timer.remove_event(self.IFS_expire_event)

		if self in packet.destination: # when this sensor is one of the receivers
			if packet.packet_type=="ACK": # an ack has been received
				statistics_collection.collector.register_successful_transmission(self.queue[0],self.timer.current_time)
				statistics_collection.collector.delay_register(self.queue[0].cal_delay(self.timer.current_time))
				self.queue.pop(0)
				# time.sleep(5)
				if self.queue and self.channel_state=="Idle": # wait for an DIFS to start back off
					new_event=event.Event("IFS expire",self.timer.current_time+self.timer.DIFS)
					new_event.register_device(self)
					self.timer.register_event(new_event)
					self.IFS_expire_event=new_event
					self.backoff_stage=self.CWmin
					self.backoff_timer=random.randint(0,self.backoff_stage-1)
				elif not self.queue:
					self.status="Sleep"
			if packet.packet_type=="CTS": # send the data to AP
				self.packet_to_send=self.queue[0]
				new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
				new_event.register_device(self)
				self.timer.register_event(self.new_event)
			if self.time_out_event!=None: # clear the time out event
				self.timer.remove_event(self.time_out_event)
				self.time_out_event=None
		else: # when the sensor is not the one of the receivers
			if self.time_out_event!=None: #collsion happens
				# print("collsion!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
				# time.sleep(2)
				statistics_collection.collector.register_collision()
				self.backoff_stage=min(self.backoff_stage*2,self.CWmax)
				self.backoff_timer=random.randint(0,self.backoff_stage-1)
				self.timer.remove_event(self.time_out_event)
				self.time_out_event=None
			if self.suspend_enabled==True and packet.packet_type=="Data": # suspend the timer
				self.backoff_timer+=random.randint(0,self.backoff_stage-1-self.backoff_timer)
			self.__NAV_renew__(packet)
		return True