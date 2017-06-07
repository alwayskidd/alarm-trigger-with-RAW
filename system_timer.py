#import event
#from collections import deque

class SystemTimer():
	"""docstring for systemTimer"""
	def __init__(self, end_time):
		self.end_time=end_time # in us
		self.current_time=0 # in us
		self.slot_time=52 #in us, 24.3.14 in the draft 5.0
		self.SIFS=160 # in us, https://mentor.ieee.org/802.11/dcn/12/11-12-1104-02-00ah-11ah-interframe-spacing-values.pptx
		self.DIFS=264 # in us, in 3.9 of doc.:IEEE 8021.11-11/1137r15
		self.ACK_time=750 #14*40 # in us, using 150kbps, packet size 100 bytes, NDP_ACK 14*40 us, +SIFS
		self.EIFS=self.SIFS+self.DIFS+self.ACK_time
		self.events=[]
		self.backoff_status="Off"

	def register_event(self,event,print_on=False): # register an event in the timeline
		import copy
		if event.time>self.end_time and (event.type in ["backoff start","backoff","transmission start"]):
			return 0

		events=[x for x in self.events if ((x.time==event.time) and (x.type==event.type))]
		if events:
			assert events.__len__()<=1 and event.device_list.__len__()<=1
			events[0].register_device(event.device_list[0])
			assert id(event)!=id(events[0])
		else:
			temp=copy.copy(event)# deepcopy will replicate all the element in the object, but copy will only copy the element of event object
			temp.device_list=copy.copy(event.device_list)
			self.events.append(temp)
		if print_on:
		 	print("systemTimer.py: register "+str(event.type)+ " of time "+str(event.time)+" at "+str(event.device_list[0].AID))
		self.events.sort(key=lambda x:x.time)

	def remove_event(self,event):
		import time
		if event.time>self.end_time:
			return 0
		temp_len=event.device_list.__len__()
		flag=0
		for each_event in self.events:
			if event.time==each_event.time and event.type==each_event.type and (event.device_list[0] in each_event.device_list):
				# print("event address:"+str(id(event)))
				assert event.device_list.__len__()==1
				each_event.device_list.remove(event.device_list[0])
				if not each_event.device_list: # remove this event from the timer record
					self.events.remove(each_event)
				flag=1
				break
		assert flag==1, "remove a event does not exist "
		assert temp_len==event.device_list.__len__(), str(temp_len)+" "+str(event.device_list.__len__())
		return 0


	def get_next_events(self): #get all the events in next time point
		if self.events:
			events=[]
			self.current_time=self.events[0].time  #renew the timeline
			events.append(self.events.pop(0))
			while self.events and events[0].time==self.events[0].time:
				events.append(self.events.pop(0))
			return events