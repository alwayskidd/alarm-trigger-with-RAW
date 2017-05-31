import random, packets, event, statistics_collection
from collections import deque

class sensor:
	def __init__(self,AID,CWmin,CWmax,locations,RTS_enabled,suspend_enabled,AP):
		self.AID=AID
		self.CWmin,self.CWmax=CWmin,CWmax
		self.back_off_stage=CWmin
		self.back_off_window=random.randint(0,self.back_off_stage-1)
		self.queue=[]
		self.RTS_enabled,self.suspend_enabled=RTS_enabled,suspend_enabled # True or Flase
		self.backoff="OFF" #turn off the backoff while there are no packet to transmit, or the new arrival packet are attempting to transmit without hearing anything
		self.channel_sensing="Idle" #channel state sensed by this Sensor
		self.status="sleep" #sensors status, 'sleep' or 'transmit' or "listen" or "suspsend"
		self.x,self.y=locations[0],locations[1]
		self.AP=AP
		self.packet_in_air,self.packet_can_receive,self.time_out_event,self.start_back_off_event,self.NAV_expire_event\
			=None,None,None,None,None
		self.receiving_power=0 # mW
		self.number_of_attempts=0
		self.number_of_backoffs=0


	def generate_one_packet(self,timer):
	#generate a packet and register the next packet arrive time
		packet=packets.packets(timer,"data",self,[self.AP])
		assert self.status=="sleep"
		self.status="listen"
		print("STA "+str(self.AID)+" ["+str(self.x)+","+str(self.y)+"] turns awake at "+str(timer.current_time))
		#self.sensor_wake_up() ## has been replaced by self.status="listen"
		self.queue.append(packet)
		if self.channel_sensing=="Idle": # start backoff after an DIFS
			new_event=event.event("start backoff",timer.current_time+timer.DIFS) # the backoff function will turn on after a DIFS
			new_event.register_STA(self)
			self.start_back_off_event=new_event
			timer.register_event(new_event)

	def update_receiving_power(self,power,minimum_interference_power,timer):
		self.receiving_power=power
		if self.receiving_power>=10**(minimum_interference_power/10) and self.channel_sensing=="Idle":
			self.channel_sensing="Busy"
			self.turn_off_backoff()
			if self.start_back_off_event!=None: # stop this event
				# print(self.start_back_off_event)
				assert self.start_back_off_event.time>=timer.current_time
				timer.remove_event(self.start_back_off_event)
			self.start_back_off_event=None

		if self.receiving_power<10**(minimum_interference_power/10) and self.channel_sensing=="Busy":
			self.channel_sensing="Idle"
			# if self.status=="listen" and self.time_out_event==None and self.NAV_expire_event==None:
			if self.status=="listen" and self.time_out_event==None and self.NAV_expire_event==None: # register a start backoff event
				assert self.start_back_off_event==None
				new_event=event.event("start backoff",timer.current_time+timer.DIFS+timer.SIFS+timer.ACK_time) # EIFS, this must be ahead of the packet receiving
				new_event.register_STA(self)
				timer.register_event(new_event)
				self.start_back_off_event=new_event
			######################## correctness varification #################
			if self.time_out_event!=None:
				assert self.time_out_event.time>=timer.current_time
			if self.NAV_expire_event!=None:
				assert self.NAV_expire_event.time>=timer.current_time, [self.AID,self.NAV_expire_event.time]

	def __NAV_setting__(self,timer,packet):
		assert self.start_back_off_event==None
		NAV=packet.NAV
		if self.NAV_expire_event!=None: # remove the NAV event
			timer.remove_event(self.NAV_expire_event)
		new_event=event.event("NAV expire",timer.current_time+NAV+1)
		new_event.register_STA(self)
		timer.register_event(new_event,print_on=False)
		self.NAV_expire_event=new_event
		print("NAV is set at "+str(self.AID)+" NAV is "+str(self.NAV_expire_event.time))


	def NAV_expire(self,timer):
		print("NAV epxired at "+str(self.AID))
		if self.channel_sensing=="Idle":
			new_event=event.event("start backoff", timer.current_time+timer.DIFS)
			new_event.register_STA(self)
			timer.register_event(new_event)
			self.start_back_off_event=new_event
		self.NAV_expire_event=None

	def add_packet_receive(self,packet):
		assert self.packet_can_receive==None
		if self.status=="listen": # packet can only be received when the STA is listenning
			self.packet_can_receive=packet

	def delete_packet_receive(self,packet):
		assert packet==self.packet_can_receive
		self.packet_can_receive=None

	def back_off(self,timer):
	# back off counter count down by 1
		if self.backoff=="OFF" or not self.has_pending_packet() or self.channel_sensing=="Busy" or self.status!="listen": #backoff is OFF or no packet is pending
			return 0
		# print("called backoff at STA "+str(self.AID)+" "+str(self)+ " there are "+ str(self.queue.__len__()))
		assert self.channel_sensing=="Idle", "back_off error"
		self.back_off_window-=1
		self.number_of_backoffs+=1
		if self.back_off_window<=0: # register a transmission start event in the system time
			self.number_of_attempts+=1
			assert self.NAV_expire_event==None
			packet=self.queue[0]
			if self.RTS_enabled: # generate an RTS packet to send to the channel
				packet=packets.packets(timer,"RTS",self,[self.AP])
				self.packet_in_air=packet
				new_event=event.event("transmission start",timer.current_time)
				new_event.register_STA(self)
				timer.register_event(new_event)
			else: # send the data packet
				self.packet_in_air=packet
				new_event=event.event("transmission start",timer.current_time)
				new_event.register_STA(self)
				timer.register_event(new_event)
			self.status="transmit"
			self.packet_can_receive=None
		return 0

	def transmission_end(self,timer): # end a transmission
		self.status="listen"
		###### register a timeout event ######
		# print(self.packet_in_air)
		if self.packet_in_air.packet_type=="RTS": # generate an cts timeout
			new_event=event.event("reply timeout",timer.current_time+timer.SIFS+packets.packets(timer,"CTS",self,[self.AP]).transmission_delay()+1)
		elif self.packet_in_air.packet_type=="data": # genarate an ack timeout
			new_event=event.event("reply timeout",timer.current_time+timer.SIFS+packets.packets(timer,"ACK",self,[self.AP]).transmission_delay()+1)
		new_event.register_STA(self)
		self.time_out_event=new_event
		# self.time_out_waiting=True
		timer.register_event(new_event)
		assert self.time_out_event.STA_list, "what a fuck"
		self.packet_in_air=None
		self.turn_off_backoff()

	def received_packet(self,packet,timer): #reaction of receiving an packet
		assert self.status=="listen", "received packet while not listen"
		assert packet.source!=self
		self.packet_can_receive=None # packet has been received
		print("packet received at "+str(self.AID))

		if self.start_back_off_event!=None: #clear the backoff event, this event may be registered when channel is idle and EIFS is set
			timer.remove_event(self.start_back_off_event)
			self.start_back_off_event=None

		if self.NAV_expire_event!=None: # clear the NAV setting there
			assert self.NAV_expire_event.time>=timer.current_time
			timer.remove_event(self.NAV_expire_event)
			self.NAV_expire_event=None

		if packet.destination[0]==self:  # when receive a packet target at this STA
			print("STA "+str(self.AID)+" has received a packet from STA "+str(packet.source.AID)\
				+" which is target to itself and the packet type is "+str(packet.packet_type) )
			assert packet.packet_type=="ACK" or packet.packet_type=="CTS"
			if packet.packet_type=="ACK": # an ack has been received
				statistics_collection.collector.successful_transmission_register(self.queue[0],timer.current_time)
				statistics_collection.collector.delay_register(self.queue[0].cal_delay(timer.current_time))
				statistics_collection.collector.register_backoff_times(self.number_of_attempts,self.number_of_backoffs)
				self.queue.pop(0)
				if self.has_pending_packet() and self.channel_sensing=="Idle": # start backoff after an DIFS
					new_event=event.event("start backoff",timer.current_time+timer.DIFS)
					new_event.register_STA(self)
					timer.register_event(new_event)
					self.start_back_off_event=new_event
					self.back_off_stage=self.CWmin
					self.back_off_window=random.randint(0,self.back_off_stage-1)
				if not self.has_pending_packet():
					self.status="sleep"
				print("\n")
			if packet.packet_type=="CTS": # an CTS has been received, send the packet to the AP after an SIFS
				self.packet_in_air=self.queue[0]
				# assert self.channel_sensing=="Idle", [self.receiving_power,self.AID]
				new_event=event.event("transmission start",timer.current_time+timer.SIFS)
				new_event.register_STA(self)
				timer.register_event(new_event)
			if self.time_out_event!=None: # clear the time out event
				timer.remove_event(self.time_out_event)
				self.time_out_event=None
		else: 
			if self.time_out_event!=None: # received a packet doesn't target to me but I have a timeout event(need a AKC/CTS), it should be a collision there
				assert self.time_out_event and self.time_out_event.time>timer.current_time, self.time_out_event
				statistics_collection.collector.collision_register()
				print("sensor.py: wrong packet collision at STA "+str(self.AID))
				self.back_off_stage=min(self.back_off_stage*2,self.CWmax)
				# self.back_off_stage=self.back_off_stage*2
				self.back_off_window=random.randint(0,self.back_off_stage-1)
				timer.remove_event(self.time_out_event)
				self.time_out_event=None
			if self.suspend_enabled==True and packet.packet_type=="data":  # suspend the packet sending while suspend function is enabled
				# self.status="suspend"
				# self.back_off_stage=min(self.back_off_stage*2,self.CWmax)
				# self.back_off_stage=self.back_off_stage*2
				self.back_off_window=random.randint(0,self.back_off_stage-1-self.back_off_window)+self.back_off_window
				# self.back_off_window=random.randint(0,self.back_off_stage-1)
			self.__NAV_setting__(timer,packet)
		return 0

	def reply_timeout(self,timer): 
		assert self.time_out_event!=None, self.AID
		statistics_collection.collector.collision_register()
		self.back_off_stage=min(self.back_off_stage*2,self.CWmax)
		# self.back_off_stage=self.back_off_stage*2
		self.back_off_window=random.randint(0,self.back_off_stage-1)
		print("sensors.py: time out collision at STA "+str(self.AID))
		if self.channel_sensing=="Idle" and self.NAV_expire_event==None: # if channel is idle after an DIFS start backoff
			assert self.start_back_off_event==None, [self.AID,self.start_back_off_event.time]
			# if not self.start_back_off_event:
			# if timer.current_time+timer.DIFS>self.start_back_off_event.start_time: # renew the time to start backoff
			new_event=event.event("start backoff",timer.current_time+timer.DIFS)
			new_event.register_STA(self)
			# print("sensor.py: add 3")
			timer.register_event(new_event)
			self.start_back_off_event=new_event
		self.time_out_event=None
		# self.time_out_waiting=False
		
	def has_pending_packet(self):
		if self.queue:
			return True
		return False

	def turn_on_backoff(self):
		# assert self.channel_sensing=="Idle"
		if self.start_back_off_event:
			self.start_back_off_event=None
		if self.has_pending_packet() and self.channel_sensing=="Idle": # if the channel is idle and the STA has packet to transmit
			self.backoff="ON"
			print("STA "+str(self.AID)+" turn on its backoff counter")

	def turn_off_backoff(self):
		if self.backoff=="OFF":
			return 0
		self.backoff="OFF"
		if self.has_pending_packet() and self.status!="suspend":
			print("STA "+str(self.AID)+" turn off its backoff counter")