import statistics_collection
class Event():
	def __init__(self, event_type, start_time, duration=0):
		self.type=event_type 
		#type include:
		#	packet arrival---there is a new packet arrived at a certain STA; has no duration
		#	backoff---back off at certain time slot; has no duration
		#	transmission end---end of an packet transmission; duration is 0
		#	IFS expire---when the IFS a device is waiting for has been passed
		#   reply timeout---the event that an cts/ack/data is timeout
		#   Wakeup for a RAW--sensors wakes up according to the RAW
		#	Wakeup during open access--sensors may wakes up during the open access
		self.time=start_time
		self.device_list=[]
		self.duration=duration

	def register_device(self,STA):
		self.device_list.append(STA)

	def backoff_excute(self,device_list,timer): # excute the backoff procedure
		import AP
		assert timer.backoff_status=="On"
		if_back_off=False
		# print("backoff excute:"+str(device_list.__len__()))
		for each in device_list:
			if not isinstance(each,AP.AP):
				if_back_off=(if_back_off or each.back_off()) # check if there exist some STA are still backing off
		if if_back_off==True: # in the next slot keep backing off
			new_event=Event("backoff",timer.current_time+timer.slot_time)
			timer.register_event(new_event)
		else: # stop the backoff
			# for each in device_list:
			# 	print(str(each.AID)+":"+str(each.backoff_status))
			print("turn off the back off in the channel at "+str(timer.current_time))
			timer.backoff_status="Off"

	def transmission_end_excute(self,device_list,timer,channel): 
	# Excute the transmission end event
	# Input:
	#	device_list--the list of all devices in the simulaitons including STAs and AP
	#   timer--the system timer object
	#	channel--the system channel object
	
		print("event.py:##############  excute the event of transmission end at "+str(timer.current_time)+" STAs are ")
		for each_trans in self.device_list:
			print("STA "+str(each_trans.AID)+" location is "+str([each_trans.x,each_trans.y]))
		print("####################################################################")
		temp_packets_list=[]
		print(self.device_list)
		for each_trans in self.device_list: # end the transmission at STAs
			temp_packets_list.append(each_trans.packet_in_air)
			each_trans.transmission_end()

		for packet in temp_packets_list:
			######## check if a packet can be received by another STA #########
			for each in device_list:
				if packet==each.packet_can_receive:
					each.packet_received(packet)

		if not channel.packet_list: # record channel busy time
			statistics_collection.collector.channel_busy_time+=timer.current_time-statistics_collection.collector.last_time_idle

	def excute(self,device_list,timer,channel):
	#This function is called when this event is triggered (i.e., reaches the time that this event will happen)
	#Input
	#	device_list--all the devices in the channel
	#	timer--the system timer object
	#	channel--the system channel object 
		if self.type=="backoff":
			self.backoff_excute(device_list,timer)
		if self.type=="packet arrival": #generate one packet
			for each_STA in self.device_list:
				each_STA.generate_one_packet()
		if self.type=="IFS expire":
			for each_device in self.device_list:
				each_device.IFS_expire()
		if self.type=="reply timeout":
			from sensor import Sensor
			for each_device in self.device_list:
				assert isinstance(each_device,Sensor), "Access point has a reply timeout event"
				each_device.reply_timeout()
		if self.type=="transmission end":
			self.transmission_end_excute(device_list,timer,channel)
		if self.type=="NAV expire":
			for each_device in self.device_list:
				each_device.NAV_expire()
		if self.type=="Wakeup for RAW":
			for each_device in self.device_list:
				each_device.wakeup_in_RAW()
		if self.type=="Wakeup during open access":
			for each_device in self.device_list:
				each_device.wakeup_in_open_access()
		if self.type=="Endup RAW":
			for each_device in self.device_list:
				each_device.end_up_RAW()