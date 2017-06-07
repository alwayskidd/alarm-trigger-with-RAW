import system_timer,sensor,event,channel,AP
# import systemTimer, sensor, event, channel, AP
import statistics_collection, random, math

def initialization(amount,d_max,timer,RTS_enable,suspend_enable,CWmax,channel):
	# RTS_enable=True
	CWmin=16

	file=open("./events/station_list_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","rb")
	import pickle
	amount=pickle.load(file)
	# system_AP=AP.AP
	system_AP=AP.AP([0,0],CWmin,CWmax,timer,channel)
	STA_list=[]
	for i in range(amount): # generate sensors at certain locations
		x=pickle.load(file)
		y=pickle.load(file)
		STA_list.append(sensor.Sensor(i+1,CWmin,CWmax,[x,y],RTS_enable,suspend_enable,system_AP,timer,channel))
	file.close()
	system_AP.register_associated_STAs(STA_list)

	file=open("./events/packet_events_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","rb")
	amount=pickle.load(file)
	print("there are "+str(amount)+" packet there")
	import time
	time.sleep(1)

	for i in range(amount):
		start_time=pickle.load(file)
		AID=pickle.load(file)
		assert STA_list[AID-1].AID==AID
		new_event=event.Event("packet arrival",start_time)
		new_event.register_device(STA_list[AID-1])
			# event=pickle.load(file)
		timer.register_event(new_event)
		statistics_collection.collector.register_packet_generated()
	file.close()
	system_AP.STA_list=STA_list
	print("STA amount is "+str(STA_list.__len__()))
	return(system_AP,STA_list)

def test(RTS_enable,suspend_enable,CWmax):
	PRAWs_duration=5.3*1000
	BI=500*1000
	#STA_number=20
	CWmin=16
	# CWmax=16*(2**6)
	#packet_arrival_rate=1.0/150000 #in us
	end_time=10**7
	packet_size=20 #in bytes, this parameter is also need to be changed in packets.py
	STA_list=[]
	radius=1000
	amount=500 # the total number of stations, it is used to read the corresponding files
	d_max=400

	for times in range(0,5):
		print("system end time="+str(end_time))
	############## initialization ###########	
		timer=system_timer.SystemTimer(end_time)
		# file=open("./results/d_max="+str(d_max)+"_amount="+str(amount)+"/CWmax="+str(CWmax)+\
		# 	"_suspend="+str(suspend_enable)+"_round="+str(times)+"_new.txt","w")
		file=open("./results/d_max="+str(d_max)+"_amount="+str(amount)+"/CWmax="+str(CWmax)+\
			"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
		# file=open("./results/CWmax/CWmax="+str(CWmax)+\
		#  	"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
		# file=open("./results/d_max="+str(d_max)+"_amount="+str(amount)+"/CWmax=unlimited"+"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
		statistics_collection.collector.set_output_file(file)
		system_channel=channel.channel()
		system_AP,STA_list=initialization(amount,d_max,timer,RTS_enable,suspend_enable,CWmax,system_channel)
		system_channel.register_devices(STA_list+[system_AP])
		# system_channel=channel.channel(system_AP,STA_list)
		system_AP.channel=system_channel
		statistics_collection.collector.end_time=end_time

	############# excute the simualtion ####################
		while  timer.events: #simulation starts
			current_events=timer.get_next_events()
			for each_event in current_events:
				if each_event.time>timer.end_time: # end the pragram
					break
				# if each_event.type!="backoff":
				print("\nThe event type is "+each_event.type)
				each_event.excute(STA_list+[system_AP],timer,system_channel)	#### !!!!!
				counter=[]
				for each in STA_list:
					if each.status!="Sleep":
						counter.append(each.AID)
				# if each_event.type!="backoff":
					# print("The event type is "+each_event.type)
				print("There are "+str(counter.__len__())+" STAs are competing for the channel at "+str(timer.current_time)+" :"+str(counter))

				counter=[]
				for each in system_channel.transmission_STA_list:
					counter.append(each.AID)

				# if each_event.type=="transmission end": # collect the backoff stage information
				# 	stage=0
				# 	counter=0
				# 	for each in STA_list:
				# 		if each.has_pending_packet():
				# 			stage+=each.back_off_stage
				# 			counter+=1
				# 	if counter>0:
				# 		statistics_collection.collector.backoff_stage_collect(stage/counter,timer.current_time,counter) # record the average backoff stage and # of contention STAs
			if statistics_collection.collector.number_of_packet==statistics_collection.collector.successful_transmissions.__len__(): # stop the simulation
				statistics_collection.collector.end_time=timer.current_time
				timer.events=[]
		# for each in STA_list:
		# 	if each.has_pending_packet():
		# 		statistics_collection.collector.register_backoff_times(each.number_of_attempts,each.number_of_backoffs)
		if system_channel.packet_list: # renewe the channel busy time
			statistics_collection.collector.channel_busy_time+=timer.end_time-statistics_collection.collector.last_time_idle

		statistics_collection.collector.print_statistics_of_delays()
		statistics_collection.collector.print_other_statistics(end_time,packet_size)
		statistics_collection.collector.clear()
		file.close()

for i in range(6,7):
	test(RTS_enable=False,suspend_enable=True,CWmax=16*(2**i))
# test(RTS_enable=False,suspend_enable=False,CWmax=16)
