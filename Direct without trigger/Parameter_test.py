import system_timer,sensor,event,channel,AP,block,initialization
import statistics_collection, random, math, os



def test(d_max,threshold,detection_time):
    end_time=10**7*2
    packet_size=100
    STA_list=[]
    radius=1000
    amount=500
    CWmax=1024
    for times in range(1):
        timer=system_timer.SystemTimer(end_time)
        folder_name="./Parameter_test/Thr="+str(threshold)+"_T="+str(detection_time/10**3)
        if not os.path.isdir(folder_name):
            os.makedirs(folder_name)
        file=open(folder_name+"/d_max="+str(d_max)+"_round="+str(times)+".txt",'w')
        statistics_collection.collector.set_output_file(file)
        system_channel=channel.channel()
        AP,STA_list=initialization.init(amount,d_max,timer,False,False,CWmax,
            system_channel,threshold,detection_time)
        AP.block_list=initialization.AID_assignment(STA_list)
        system_channel.register_devices(STA_list+[AP])
        AP.channel=system_channel
        AP.max_data_size=packet_size
        statistics_collection.collector.end_time=end_time
        ################# start the simulation ##################
        while timer.events:
            current_events=timer.get_next_events()
            for each_event in current_events:
                if each_event.type!="backoff":
                    print("The event type is "+each_event.type+" at "+str(timer.current_time))
                if each_event.time>timer.end_time:
                    break
                each_event.execute(STA_list+[AP],timer,system_channel)
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
            if (statistics_collection.collector.number_of_packet==
                statistics_collection.collector.successful_transmissions.__len__()): 
                if not [x for x in timer.events if x.type=="Polling round end"]:# stop the simulation
                    statistics_collection.collector.end_time=timer.current_time
                    timer.events=[]
        if system_channel.packet_list: # renew the channel busy time
            statistics_collection.collector.channel_busy_time+=(timer.end_time-
                statistics_collection.collector.last_time_idle)
        assert statistics_collection.collector.successful_transmissions==statistics_collection.collector.number_of_packet
        statistics_collection.collector.print_statistics_of_delays()
        statistics_collection.collector.print_polling_info()
        statistics_collection.collector.print_other_statistics(end_time,packet_size)
        
        statistics_collection.collector.clear()
        file.close()
        os.system('cls' if os.name == 'nt' else 'clear')

import numpy as np
for threshold in np.arange(0.5,1,0.1):
    for detection_time in range(300*10**3,500*10**3,50*10**3):
        for d_max in range(1900,1901,300):
            test(d_max,threshold,detection_time)