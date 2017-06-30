import system_timer,sensor,event,channel,AP,block,initialization
import statistics_collection, random, math, os
def test(RTS_enable,suspend_enable,CWmax):
    PRAWs_duration=5.3*1000
    BI=500*1000
    #STA_number=20
    CWmin=15
    # CWmax=16*(2**6)
    #packet_arrival_rate=1.0/150000 #in us
    end_time=10**6*5
    packet_size=40 #in bytes, this parameter is also need to be changed in packets.py
    STA_list=[]
    radius=1000
    amount=500 # the total number of stations, it is used to read the corresponding files
    d_max=1900

    for times in range(0,50):
        print("system end time="+str(end_time))
        ############## initialization ###########
        timer=system_timer.SystemTimer(end_time)
        # file=open("./results/d_max="+str(d_max)+"_amount="+str(amount)+"/CWmax="+str(CWmax)+\
        # 	"_suspend="+str(suspend_enable)+"_round="+str(times)+"_new.txt","w")
        folder_name="./results/d_max="+str(d_max)+"_amount="+str(amount)
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        file=open(folder_name+"/packet_size="+str(packet_size)+"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
        # file=open("./results/CWmax/CWmax="+str(CWmax)+\
        #  	"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
        # file=open("./results/d_max="+str(d_max)+"_amount="+str(amount)+"/CWmax=unlimited"+"_suspend="+str(suspend_enable)+"_round="+str(times)+".txt","w")
        statistics_collection.collector.set_output_file(file)
        system_channel=channel.channel()
        system_AP,STA_list=initialization.init(amount,d_max,timer,RTS_enable,suspend_enable,CWmax,system_channel)
        system_AP.block_list=initialization.AID_assignment(STA_list)
        system_channel.register_devices(STA_list+[system_AP])
        system_AP.channel=system_channel
        statistics_collection.collector.end_time=end_time

        ############# excute the simualtion ####################
        while  timer.events: #simulation starts
            current_events=timer.get_next_events()
            for each_event in current_events:
                if each_event.type!="backoff":
                    print("The event type is "+each_event.type+" at "+str(timer.current_time))
                if each_event.time>timer.end_time: # end the pragram
                    break
                each_event.execute(STA_list+[system_AP],timer,system_channel)	#### !!!!!
                if each_event.type!="backoff":
                    counter=[]
                    for each in STA_list: # how many STAs stay awake
                        if each.status!="Sleep":
                            counter.append(each.AID)
                    print("There are "+str(counter.__len__())+" STAs stays awake at "
                        +str(timer.current_time))
                    counter=[]
                    backoff_timer=[]
                    for each in STA_list:
                        if not (each.backoff_status=="Off" or not each.queue or each.status!="Listen"):
                            counter.append(each.AID)
                            backoff_timer.append(each.backoff_timer)
                    print("There are "+str(counter.__len__())+" STAs are competing for the channel at "
                        +str(timer.current_time))
                    print("The backoff timers are "+str(backoff_timer)+"\n ")
                    # counter=[]
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
                if not [x for x in timer.events if x.type=="Polling round end"]:
                    statistics_collection.collector.end_time=timer.current_time
                    timer.events=[]
        # for each in STA_list:
        # 	if each.has_pending_packet():
        # 		statistics_collection.collector.register_backoff_times(each.number_of_attempts,each.number_of_backoffs)
        if system_channel.packet_list: # renewe the channel busy time
            statistics_collection.collector.channel_busy_time+=timer.end_time-statistics_collection.collector.last_time_idle

        statistics_collection.collector.print_statistics_of_delays()
        print("\n")
        statistics_collection.collector.print_other_statistics(end_time,packet_size)
        print("\n")
        statistics_collection.collector.print_polling_info()
        statistics_collection.collector.clear()
        file.close()

for i in range(6,7):
    test(RTS_enable=False,suspend_enable=False,CWmax=16*(2**i)-1)
# test(RTS_enable=False,suspend_enable=False,CWmax=16)
