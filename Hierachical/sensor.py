import event,device,packet,system_timer
import random,statistics_collection

class Sensor(device.Device):
    def __init__(self,AID,CWmin,CWmax,locations,RTS_enabled,suspend_enabled,AP,timer,channel):
        device.Device.__init__(self,locations,CWmin,CWmax,timer,channel)
        self.RTS_enabled,self.suspend_enabled=RTS_enabled,suspend_enabled # True or False
        # self.packet_to_send=None
        self.AID=AID
        self.AP=AP
        self.access_mode="Open access" # the access mechanism is used currently
        self.next_RAW_slot,self.next_open_access=None,None # the restricted window this sensor is currently involved
        self.receiving_power=0 # mW
        self.RAW_CWmin,self.RAW_CWmax=7,15  #the contention window parameter within a RAW
        self.open_access_CWmin,self.open_access_CWmax=15,1023 #the contention window parameter in open access
        self.freezed_backoff_timer,self.freezed_backoff_stage=None,None
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
            # self.packet_to_send=new_packet

    def back_off(self):
        #This function is called when a backoff time slot has passed
        #This sensor's backoff timer is count down in this function and transmission is triggered when timer<=0
        #Output:
        #	True--this sensor is still backing off
        #	False--this senosr is not
        # print("I am backing off")
        if (self.backoff_status=="Off" or not self.queue or self.status!="Listen"): # backoff timer will not decrease
            return False
        assert self.channel_state=="Idle", "channel is busy while back off is not turned off"
        if self.access_mode=="General Raw": # calculate the expected time to transmit a data frame and get the ack
            expected_time=(self.timer.slot_time*self.backoff_timer+self.queue[0].transmission_delay()+self.timer.SIFS
                +self.timer.NDP_time)
        elif self.access_mode=="Trigger Raw": # calculate the expected time to transmit a PS-POLL frame and get the ACK
            expected_time=(self.timer.slot_time*self.backoff_timer+self.timer.NDP_time*2+self.timer.SIFS)
        if "Raw" in self.access_mode:
            # print(expected_time)
            if self.timer.current_time+expected_time>self.next_RAW_slot.end_time:
               self.backoff_status="Off"
               return False
        self.backoff_timer-=1
        if self.backoff_timer<=0: # transmit this packet immediately
            if self.access_mode=="Trigger Raw": # transmit a ps-poll frame
                new_packet=packet.Packet(self.timer,"NDP Ps-poll",self,[self.AP])
                self.transmit_packet(new_packet)
            else:
                if self.RTS_enabled: # transmit a RTS frame
                    new_packet=packet.Packet(self.timer,"RTS",self,[self.AP])
                    self.transmit_packet(new_packet)
                else: # transmit the data packet
                    new_packet=self.queue[0]
                    self.transmit_packet(new_packet)
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
        elif self.packet_in_air.packet_type=="Data" or self.packet_in_air.packet_type=="NDP Ps-poll": 
        # sensor need to wait an ACK timeout
            new_event=event.Event("reply timeout",self.timer.current_time+self.timer.SIFS+
                packet.Packet(self.timer,"NDP ACK",self,[self.AP]).transmission_delay()+1)
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
        assert self.channel_state=="Idle", "IFS expired while the channel is busy STA AID is %d" % self.AID
        self.IFS_expire_event=None
        if self.packet_to_send==None: #start backoff counter as no packet need to be sent
            self.backoff_status="On"
            if self.timer.backoff_status=="Off": # register a backoff event
                new_event=event.Event("backoff",self.timer.current_time+self.timer.slot_time)
                new_event.register_device(self)
                self.timer.register_event(new_event)
                self.timer.backoff_status="On"
                print("backoff is on")
        elif (self.channel_state=="Idle" or self.packet_to_send.packet_type=="NDP ACK" or
        self.packet_to_send.packet_type=="CTS"): # start a transmission for the pending packet
            self.transmit_packet(self.packet_to_send)
            self.packet_to_send=None


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
            if packet.packet_type=="NDP ACK": # an ack has been received
                self.__received_ACK__()
            elif packet.packet_type=="CTS": # send the data to AP
                self.__received_CTS__()
            elif packet.packet_type=="Beacon Frame": 
                self.__received_Beacon__(packet)
            if self.time_out_event!=None: # clear the time out event
                self.timer.remove_event(self.time_out_event)
                self.time_out_event=None
        else: # when the sensor is not the one of the receivers
            if self.time_out_event!=None: #collsion happens
                statistics_collection.collector.register_collision()
                self.backoff_stage=min(self.backoff_stage*2,self.CWmax)
                self.backoff_timer=random.randint(0,self.backoff_stage-1)
                self.timer.remove_event(self.time_out_event)
                self.time_out_event=None
            if self.suspend_enabled==True and packet.packet_type=="Data": # suspend the timer
                self.backoff_timer+=random.randint(0,self.backoff_stage-1-self.backoff_timer)
            self.__NAV_renew__(packet)
        return True

    def __received_ACK__(self):
    # This function is called when the sensor received an ACK from AP
        if self.last_packet_sent.packet_type=="Data":
            statistics_collection.collector.register_successful_transmission(self.queue[0],self.timer.current_time)
            statistics_collection.collector.delay_register(self.queue[0].cal_delay(self.timer.current_time))
            self.queue.pop(0)
            if self.queue and self.channel_state=="Idle": # wait for an DIFS to start back off
                new_event=event.Event("IFS expire",self.timer.current_time+self.timer.DIFS)
                new_event.register_device(self)
                self.timer.register_event(new_event)
                self.IFS_expire_event=new_event
                self.backoff_stage=self.CWmin
                self.backoff_timer=random.randint(0,self.backoff_stage-1)
            elif not self.queue:
                self.status="Sleep"

    def __received_CTS__(self):
    # This function is called when the sensor received an CTS from AP
        self.packet_to_send=self.queue[0]
        new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
        new_event.register_device(self)
        self.timer.register_event(new_event)

    def __received_Beacon__(self,beacon):
    # This function is called when the sensor received a Beacon frame from AP
        self.next_RAW_slot=None
        self.next_open_access=0
        for each_RAW in beacon.RAWs:# check whether the STA is in a certain RAW
            if ((each_RAW.paged_only and self in each_RAW.paged_STAs) or 
                (not each_RAW.paged_only and self in each_RAW.STAs)): # find the corresonding slot in this RAW for the sensor
                for each_slot in each_RAW.slot_list:
                    if self in each_slot.STAs:
                        self.next_RAW_slot=each_slot
                        break
                        
        self.next_open_access=max(x.end_time for x in beacon.RAWs)
        self.status="Sleep"
        if self.next_RAW_slot!=None: # wake up at certain time for this RAW
            new_event=event.Event("Wakeup for RAW", self.next_RAW_slot.start_time)
            new_event.register_device(self)
            self.timer.register_event(new_event)
            return True
        else: # wake up while the channel is open for access
            new_event=event.Event("Wakeup during open access",self.next_open_access)
            new_event.register_device(self)
            self.timer.register_event(new_event)
            return False


    def wakeup_in_RAW(self):
    # This function is called when the sensor wakesup in a RAW
    # The first backoff timer need to be freezed and the second backoff timer with RAW_CWmin RAW_CWmax
    # Output:
    #	True--the sensor has something to report
    #	False--the sensor has nothing to report
        # print("wake up at "+str(self.timer.current_time))
        import random
        if not self.queue: # if there is no packet buffering here
            return False
        assert self.next_RAW_slot.start_time==self.timer.current_time, "wake up in a wrong RAW"
        if self.next_RAW_slot.raw_type=="General":
            self.access_mode="General Raw"
        elif self.next_RAW_slot.raw_type=="Trigger":
            self.access_mode="Trigger Raw"
        # print(self.access_mode)
        self.status="Listen"
        # use the new backoff timer value
        self.CWmin,self.CWmax=self.RAW_CWmin,self.RAW_CWmax
        self.freezed_backoff_timer=self.backoff_timer
        self.freezed_backoff_stage=self.backoff_stage
        self.backoff_timer=random.randint(0,self.CWmin)
        self.backoff_stage=self.CWmin
        if self.channel_state=="Idle": # start backoff after DIFS
            new_event=event.Event("IFS expire",self.timer.DIFS+self.timer.current_time)
            new_event.register_device(self)
            self.timer.register_event(new_event)
            self.IFS_expire_event=new_event
        new_event=event.Event("Endup RAW",self.next_RAW_slot.end_time) # end this RAW
        new_event.register_device(self)
        self.timer.register_event(new_event)
        return True

    def end_up_RAW(self):
        # This function is called when the sensor end up with current involved RAW
        # Output:
        #	True--the sensor will wake up for the next open access period
        #	False--the sensor will stay sleep
        # exit(0)
        if not self.queue: # go back to sleep mode
            self.status="Sleep"
            return False
        assert self.next_open_access>=self.timer.current_time, "end_up_RAW function i sensor.py"
        new_event=event.Event("Wakeup during open access",self.next_open_access)
        new_event.register_device(self)
        self.timer.register_event(new_event)
        self.next_open_access=None
        self.next_RAW_slot=None
        self.status="Sleep"
        return True

    def wakeup_in_open_access(self):
        # This function is called when the sensor wakes up in an open access period
        # Output:
        #	True--the sensor has waken up
        #	False--the sensor keeps sleep
        if not self.queue:
            return False
        self.access_mode="Open access"
        self.status="Listen"
        self.CWmin,self.RAW_CWmax=self.open_access_CWmin,self.open_access_CWmax
        if self.freezed_backoff_timer!=None and self.freezed_backoff_stage!=None: # recover the backoff timer
            self.backoff_timer,self.backoff_stage=self.freezed_backoff_timer,self.freezed_backoff_stage
        if self.channel_state=="Idle":
            new_event=event.Event("IFS expire",self.timer.DIFS+self.timer.current_time)
            new_event.register_device(self)
            self.timer.register_event(new_event)
            self.IFS_expire_event=new_event
        return True