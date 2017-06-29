import packet,event,device,restricted_access_window,alarm_detector
import time
class  AP(device.Device): # has no  downlink traffic there
    def __init__(self,locations,CWmin,CWmax,timer,channel):
        device.Device.__init__(self,locations,CWmin,CWmax,timer,channel)
        self.AID=0
        self.status="Listen" # AP status: listen or transmit
        self.STA_list=[]
        self.busy_cannot_decode_start=None
        self.idle_start=0
        self.packet_has_received=[]
        self.mode="Open access" # Open access or Alarm resolution
        self.max_data_size=40 # bytes
        self.block_list=None
        self.polling_round=None
        self.detector=alarm_detector.AlarmDetector(timer,300*10**3)

    def register_associated_STAs(self,STA_list):
        self.STA_list=STA_list

    def packet_received(self,received_packet):
    # This function is called when AP receives an packet from some STAs
    # Input:
    #	packet--the received packet at AP
        if self in received_packet.destination:
            if received_packet.packet_type=="RTS":
                self.packet_to_send=packet.Packet(self.timer,"CTS",self,[received_packet.source])
            if received_packet.packet_type=="Data" or received_packet.packet_type=="NDP Ps-poll":
                self.packet_to_send=packet.Packet(self.timer,"NDP ACK",self,[received_packet.source])
                self.packet_has_received.append(received_packet)
                if self.mode=="Open access" and self.detector.frame_received(received_packet): # register an alarm detect event
                    new_event=event.Event("Alarm detected",self.timer.current_time)
                    new_event.register_device(self)
                    self.timer.register_event(new_event)
                if received_packet.packet_type=="Data": # record report from this STA is received
                    self.block_list.report_received(received_packet)
            new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
            new_event.register_device(self)
            self.timer.register_event(new_event)
            self.IFS_expire_event=new_event
            self.packet_can_receive=None
            if self.mode=="Alarm resolution--Polling phase":
                self.current_slot.status="Received"

    def IFS_expire(self):
    # This function is called AP has wait for an IFS, (most likely the SIFS)
    # The pending packet will be send
        if self.packet_to_send!=None: #may be the EIFS expired
            self.transmit_packet(self.packet_to_send)
            self.packet_to_send=None
        self.IFS_expire_event=None

    def transmission_end(self):
    # This function is called when AP finished its transmission
        self.channel.clear_transmission_in_air(self.packet_in_air)
        if self.packet_in_air.destination==self.STA_list:
            print("packet from AP is broadcasted and the frame type is "+self.packet_in_air.packet_type)
            time.sleep(1)
        else:
            print("packet from AP to STA "+str(self.packet_in_air.destination[0].AID)+
    	   " has been transmitted, packet type is "+self.packet_in_air.packet_type)
        self.packet_in_air=None
        self.status="Listen"
        if self.queue:
            self.queue.pop(0)
            if self.queue:
                new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
                new_event.register_device(self)
                self.timer.register_event(new_event)
                self.packet_to_send=self.queue[0]
            elif self.mode=="Alarm resolution--clear the channel":
                self.__transit_to_polling_phase__()
            else:
                time.sleep(10)
        return 0

    def update_receiving_power(self,packets_in_air):
    #This function is called when the power level in the channel has been changed
    #The channel status will be changed by judging whether the power level reaches the minimum interference power
    #Input:
    #	packets_in_air: the list of packets that are transmitting in the air
    #Output:
    #	True--channel status is changed from idle/busy to busy/idle
    #	False--channel status is not changed
        status_changed=super().update_receiving_power(packets_in_air)
        if self.channel_state=="Busy":
            if self.detector.channel_busy():
                new_event=event.Event("Alarm detected",self.timer.current_time)
                new_event.register_device(self)
                self.timer.register_event(new_event)
                self.mode="Alarm resolution--clear the channel"
        elif self.channel_state=="Idle":
            if self.detector.channel_idle():
                new_event=event.Event("Alarm detected",self.timer.current_time)
                new_event.register_device(self)
                self.timer.register_event(new_event)
                self.mode="Alarm resolution--clear the channel"
        if self.mode=="Alarm resolution--Polling phase" and self.current_slot!=None:
            if self.current_slot.status=="Idle" and self.channel_state=="Busy": # change the slot status to collision (may becomes Received)
                self.current_slot.status="Collision"
        return status_changed

    def update_packet_can_receive(self,new_packet):
        super().update_packet_can_receive(new_packet)
        if self.packet_can_receive!=None:
            print("the souce of packet can receive:"+str([self.packet_can_receive.source.x,self.packet_can_receive.source.y])
                +" "+str(self.packet_can_receive.source.AID))
            signal_power=self.channel.rx_power_at_STA(self.packet_can_receive.source,self)
            signal_power=10**(signal_power/10)
            interference_power=self.receiving_power-signal_power
            print("signal power is "+str(signal_power))
            print("interference power is "+str(interference_power))

    def alarm_detected(self):
    #This function is called when the alarm event is detected
        import math
        self.detector.turn_off()
        self.mode="Alarm resolution--clear the channel"
        self.busy_cannot_decode_start=None
        ############ calculate how many beacons need to be announced continuously to ensure every sensor can received the beacon#######
        transmission_finish_time=packet.Packet(self.timer,"Data",self,self.STA_list,
        size=self.max_data_size).transmission_delay() # This time ensures that all the current transmission will be finished
        tmp=restricted_access_window.RAW("General",False)
        duration_for_beacon=self.timer.SIFS+packet.BeaconFrame([tmp],self.timer,self,self.STA_list).transmission_delay()
        number_of_beacons=math.ceil((transmission_finish_time+self.timer.SIFS)/duration_for_beacon) #cal the number of beacons needed
        end_time_for_clearance=number_of_beacons*duration_for_beacon+self.timer.current_time-self.timer.SIFS
        for i in range(1,number_of_beacons+1): # put the needed beacons in the queue
            start_time_of_RAW=self.timer.current_time+duration_for_beacon*i-self.timer.SIFS
            RAW=restricted_access_window.RAW("General",False)
            RAW.parameter_setting(start_time_of_RAW,end_time_for_clearance-start_time_of_RAW,1,self.STA_list)
            new_beacon=packet.BeaconFrame([RAW],self.timer,self,self.STA_list)
            self.queue.append(new_beacon)
        print("number of beacons:"+str(number_of_beacons))
        time.sleep(2)
        self.transmit_packet(self.queue[0])

    def __transit_to_polling_phase__(self):
    # This function is called when channel is cleard by consecutive beacons
    # and need to transit into polling phase to resolve the alarm reports
        print("\n #####################Transit into the pollling phase######################")
        time.sleep(2)
        self.current_slot=None
        temp,blocks_to_check=self.block_list.get_blocks_at_certain_level(0),[]
        for each in temp:
            if not each.block_finished: # this the packets in block have not been all received, check this block
                blocks_to_check.append(each)

        print(blocks_to_check.__len__())
        self.polling_round=restricted_access_window.PollingRound(self.timer,self.max_data_size,
            self,self.STA_list)
        self.polling_round.set_polling_target([],[],blocks_to_check)
        self.queue=self.polling_round.generate_beacon(self.timer.current_time+self.timer.SIFS,
            self.channel_state,self.max_data_size)
        ######### send the beacon frame after an SIFS ############
        new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
        new_event.register_device(self) # register to send the beacon after an SIFS
        self.timer.register_event(new_event)
        self.IFS_expire_event=new_event
        self.packet_to_send=self.queue[0]
        ######### record when the RAW slots will start ################
        for each_RAW in self.polling_round.RAWs:
            for each_slot in each_RAW.slot_list: # register when the RAW slot start event
                new_event=event.Event("Raw slot start",each_slot.start_time)
                new_event.register_device(self)
                self.timer.register_event(new_event)
        ######## record when the polling round will end ###############
        new_event=event.Event("Polling round end",self.polling_round.end_time) # register when the polling round will end
        new_event.register_device(self)
        self.timer.register_event(new_event)
        self.mode="Alarm resolution--Polling phase"
        

    def RAW_slot_start(self):
    # This function is called when a RAW slot starts
        print("##################### A RAW start ######################### at "+str(self.timer.current_time))
        self.current_slot=self.polling_round.find_current_slot(self.timer.current_time)
        print("RAW type is "+str(self.current_slot.raw_type))
        self.current_slot.status="Idle"

    def polling_round_end(self):
    # This function is called when polling round ends
        self.current_slot=None
        RAW_slots=[]
        for each_RAW in self.polling_round.RAWs:
            for each_slot in each_RAW.slot_list:
                RAW_slots.append(each_slot)
        print([x.status for x in RAW_slots])
        next_STAs_to_check,next_STAs_to_collect,next_blocks_to_check=self.polling_round.polling_round_analyse()
        if not (next_STAs_to_collect or next_STAs_to_check or next_blocks_to_check):
            self.mode="Open access"
            self.detector.reset()
            self.detector.turn_on()
        self.polling_round=restricted_access_window.PollingRound(self.timer,self.max_data_size,self,self.STA_list)
        self.polling_round.set_polling_target(next_STAs_to_check,next_STAs_to_collect,next_blocks_to_check)
        self.queue=self.polling_round.generate_beacon(self.timer.current_time,#+self.timer.SIFS,
            self.channel_state,self.max_data_size)
        # new_event=event.Event("IFS expire",self.timer.current_time+self.timer.SIFS)
        # new_event.register_device(self) # register to send the beacon after an SIFS
        # self.timer.register_event(new_event)
        # self.IFS_expire_event=new_event
        # self.packet_to_send=self.queue[0]
        self.transmit_packet(self.queue[0])
        for each_RAW in self.polling_round.RAWs:
            for each_slot in each_RAW.slot_list: # register when the RAW slot start event
                new_event=event.Event("Raw slot start",each_slot.start_time)
                new_event.register_device(self)
                self.timer.register_event(new_event)
        new_event=event.Event("Polling round end",self.polling_round.end_time) # register when the polling round will end
        new_event.register_device(self)
        self.timer.register_event(new_event)
        time.sleep(5)
        print("\n##############################next polling round##########################################")