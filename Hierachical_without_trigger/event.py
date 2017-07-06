import statistics_collection
class Event():
    def __init__(self, event_type, start_time,duration=0):
        self.type=event_type 
        #type include:
        #	packet arrival---there is a new packet arrived at a certain STA; has no duration
        #   transmit packet---transmit frames into the air
        #	backoff---back off at certain time slot; has no duration
        #	transmission end---end of an packet transmission; duration is 0
        #	IFS expire---when the IFS a device is waiting for has been passed
        #   reply timeout---the event that an cts/ack/data is timeout
        #   Wakeup for a RAW--sensors wakes up according to the RAW
        #	Wakeup during open access--sensors may wakes up during the open access
        #   Raw slot start--a raw start
        #   Polling round end--a polling round is ended
        #   NAV expire--the NAV is time out
        #   Endup RAW--the event that a RAW is end up
        self.time=start_time
        self.device_list=[]
        self.duration=duration
        priorities={
            "transmit packet": 4,
            "packet arrival": 0,
            "backoff": 1,
            "transmission end": 1,
            "IFS expire": 1,
            "reply timeout": 1,
            "NAV expire":1,
            "Wakeup for RAW": 2,
            "Endup RAW":0,
            "Raw slot start": 3,
            "Wakeup during open access": 2,
            "Polling round end":1,
            "Alarm detected": 0
        }
        self.priority=priorities[self.type]

    def register_device(self,STA):
        self.device_list.append(STA)

    def backoff_execute(self,device_list,timer): # excute the backoff procedure
        import AP
        assert timer.backoff_status=="On"
        if_back_off=False
        # print("backoff excute:"+str(device_list.__len__()))
        for each in device_list:
            if not isinstance(each,AP.AP):
                if_back_off=(each.back_off() or if_back_off) # check if there exist some STA are still backing off
        if if_back_off==True: # in the next slot keep backing off
            new_event=Event("backoff",timer.current_time+timer.slot_time)
            timer.register_event(new_event)
        else: # stop the backoff
            print("turn off the back off in the channel at "+str(timer.current_time))
            timer.backoff_status="Off"

    def transmission_end_execute(self,device_list,timer,channel): 
    # Excute the transmission end event
    # Input:
    #	device_list--the list of all devices in the simulaitons including STAs and AP
    #   timer--the system timer object
    #	channel--the system channel object
        temp_packets_list=[]
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

    def execute(self,device_list,timer,channel):
    #This function is called when this event is triggered (i.e., reaches the time that this event will happen)
    #Input
    #	device_list--all the devices in the channel
    #	timer--the system timer object
    #	channel--the system channel object 
        if self.type=="backoff":
            self.backoff_execute(device_list,timer)
        elif self.type=="transmission end":
            self.transmission_end_execute(device_list,timer,channel)
        elif self.type=="transmit packet":
            new_packets=[]
            for each_device in self.device_list:
                new_packets.append(each_device.packet_in_air)
                print("A packet from STA "+str(each_device.AID)+" is transmitted in the air")
            channel.register_transmission_in_air(new_packets)
        elif self.type=="Alarm detected":
            for each_device in self.device_list:
                each_device.alarm_detected()
        else:
            for each_device in self.device_list:
                function_list={'packet arrival': each_device.generate_one_packet,
                'IFS expire': each_device.IFS_expire,
                'reply timeout': each_device.reply_timeout,
                'NAV expire': each_device.NAV_expire,
                'Wakeup for RAW': each_device.wakeup_in_RAW,
                'Wakeup during open access': each_device.wakeup_in_open_access,
                'Endup RAW': each_device.end_up_RAW,
                "Raw slot start": each_device.RAW_slot_start,
                "Polling round end": each_device.polling_round_end
                }
                function_list[self.type]()