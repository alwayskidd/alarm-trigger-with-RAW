#import event
#from collections import deque

class systemTimer():
	"""docstring for systemTimer"""
	def __init__(self, end_time):
		self.end_time=end_time # in us
		self.current_time=0 # in us
		self.slot_time=52 #in us, 24.3.14 in the draft 5.0
		self.SIFS=160 # in us, https://mentor.ieee.org/802.11/dcn/12/11-12-1104-02-00ah-11ah-interframe-spacing-values.pptx
		self.DIFS=264 # in us, in 3.9 of doc.:IEEE 8021.11-11/1137r15
		self.ACK_time=750 #14*40 # in us, using 150kbps, packet size 100 bytes, NDP_ACK 14*40 us, +SIFS
		self.events=[]
		self.backoff_status="OFF"

	def register_event(self,event,print_on=False): # register an event in the timeline
		import copy
		if event.time>self.end_time and (event.type in ["backoff start","backoff","transmission start"]):
			print("ca")
			return 0

		events=[x for x in self.events if ((x.time==event.time) and (x.type==event.type))]
		if events:
			assert events.__len__()<=1 and event.STA_list.__len__()<=1
			events[0].register_STA(event.STA_list[0])
			assert id(event)!=id(events[0])
		else:
			# print("event STA list "+str(id(event.STA_list)))
			# print(event.STA_list)
			#temp=event.event()
			temp=copy.copy(event)# deepcopy will replicate all the element in the object, but copy will only copy the element of event object
			temp.STA_list=copy.copy(event.STA_list)
			self.events.append(temp)
			# print("temp STA list "+str(id(temp.STA_list)))
			# print(temp.STA_list)
			# assert id(temp)!=id(event)
		if print_on:
		 	print("systemTimer.py: register "+str(event.type)+ " of time "+str(event.time)+" at "+str(event.STA_list[0].AID))
		self.events.sort(key=lambda x:x.time)

	def remove_event(self,event):
		if event.time>self.end_time:
			return 0
		temp_len=event.STA_list.__len__()
		flag=0
		# if event.type=="NAV expire":
		# 	print(event.type,event.STA_list)
		for each_event in self.events:
			if event.time==each_event.time and event.type==each_event.type and (event.STA_list[0] in each_event.STA_list):
				# print("event address:"+str(id(event)))
				assert event.STA_list.__len__()==1
				each_event.STA_list.remove(event.STA_list[0])
				flag=1
				# print("each event address:"+str(id(each_event)))
			if not each_event.STA_list and flag: #backoff event could have an empty STA list
				self.events.remove(each_event)
			if flag:
				break
		if flag==0:
			print("remove event "+str(event.type)+" at "+str(event.time)+" STA is "+str(event.STA_list[0].AID))
		assert flag==1, "remove a event does not exist "
		assert temp_len==event.STA_list.__len__()
		return 0


	def get_next_events(self): #get all the events in next time point
		if self.events:
			events=[]
			self.current_time=self.events[0].time  #renew the timeline
			events.append(self.events.pop(0))
			while self.events and events[0].time==self.events[0].time:
				events.append(self.events.pop(0))
			return events