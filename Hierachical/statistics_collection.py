import statistics
class statisticsCollection():
    """docstring for statistics_collection"""
    def __init__(self):
        self.delays=[]
        # self.contention_level=[]
        self.number_of_packet=0
        self.number_of_assignment=0
        self.successful_transmissions=[]
        self.collisions=0
        self.channel_busy_time=0
        self.last_time_idle=0
        # self.suspension=[]
        self.end_time=0
        self.back_off_stage=[]
        self.back_off_collection_time=[]
        self.contention_STAsN=[]
        self.average_backoffs=[]
        self.polling_phases_start=[]
        self.beacons=[]

    def register_alarm_event(self,time):
        self.polling_phases_start.append(time)

    def register_beacons(self,time,beacon):
        self.beacons.append([beacon,time])

    def register_backoff_times(self,attempts,total_backoffs):
        self.average_backoffs.append(total_backoffs/attempts)

    def backoff_stage_collect(self,stage,time,contention_STAsN):
        self.back_off_stage.append(stage)
        self.back_off_collection_time.append(time)
        self.contention_STAsN.append(contention_STAsN)

    def register_successful_transmission(self,packet,time):
        self.successful_transmissions.append([packet,time])

    def register_collision(self):
        self.collisions+=1

    def delay_register(self,delay):
        self.delays.append(delay)

    def register_packet_generated(self):
        self.number_of_packet+=1
	# def register_suspension(self,STA,time,energy,packet_source):
	# 	self.suspension.append([STA,time,energy,packet_source])
    def print_number_of_successful_transmission(self):
        print("there are "+str(self.successful_transmissions.__len__())+ " packets has been transmitted.")
        print("transmission times are: ")
        for each in self.successful_transmissions:
            print("From STA "+str(each[0].source.AID)+" at "+str(each[1]))

    def print_statistics_of_delays(self):
        if not self.delays: # error as no packet is received
            print("None of the packet is received")
            return False
        print("maximum delay is:"+str(max(self.delays)/1000)+"\n")
        if self.delays.__len__()>1:
            self.file.write("maximum delay is:"+str(max(self.delays)/1000)+"\n")
            self.file.write("minimum delay is:"+str(min(self.delays)/1000)+"\n")
            self.file.write("mean value of the delays:"+str(statistics.mean(self.delays)/1000)+"\n")
            self.file.write("standard deviation:"+str(statistics.stdev(self.delays)/1000)+"\n")
        else:
            self.file.write("standard deviation:"+str(0)+"\n")

    def print_other_statistics(self,end_time,packet_size):
        self.file.write("there are "+str(self.number_of_packet)+" packets need to be transmit.\n")
        self.file.write("there are "+str(self.successful_transmissions.__len__())+ " packets has been transmitted.\n")
        self.file.write("collisions:"+str(self.collisions)+"\n")
        self.file.write("Throughput:"+str(self.successful_transmissions.__len__()*packet_size*8/(self.end_time/10**6)/10**3)+" kbps"+"\n")
        self.file.write("Transmission successful probability:"+\
        	str(self.successful_transmissions.__len__()/(self.successful_transmissions.__len__()+self.collisions))+"\n")
        self.file.write("channel busy time:"+str(self.channel_busy_time)+"\n")
        self.file.write("The end time is "+str(self.end_time)+"\n")

    def print_polling_info(self):
        self.file.write("The AP detects alarm event for "+str(self.polling_phases_start.__len__())+
            " times.\nAlarm events is detected at "+str([x/1000 for x in self.polling_phases_start])+"\n")
        counter=0
        tmp=0
        for [each_beacon,generation_time] in self.beacons:
            polling_phase=[x for x in self.polling_phases_start if x<=generation_time]
            if len(polling_phase)>counter: # update the current polling phases
                counter=len(polling_phase)
                print("\n In the polling phase "+str(counter)+"\n")
            for each_RAW in each_beacon.RAWs:
                if each_RAW.raw_type=="Trigger":
                    self.file.write("There are "+str(len(each_RAW.paged_STAs))+" are paged to send Ps-poll. It costs "
                        +str(each_RAW.duration/1000)+" ms\n")
                if each_RAW.raw_type=="General" and each_RAW.paged_only==True:
                    self.file.write("There are "+str(len(each_RAW.paged_STAs))+" are paged to send data. It costs "+
                        str(each_RAW.duration/1000)+" ms\n")
                if each_RAW.raw_type=="General" and each_RAW.paged_only==False:
                    self.file.write("A general RAW is conducted to check if a block has data to send. It costs "+
                        str(each_RAW.duration/1000)+" ms\n")

    def clear(self):
        self.__init__()

    def set_output_file(self,file):
        self.file=file


collector=statisticsCollection()