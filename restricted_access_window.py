class RawSlot():
    """docstring for raw_slot"""
    def __init__(self,start_time,end_time,raw_type="General",cross_boundary=False):
        self.start_time=start_time
        self.end_time=end_time
        self.cross_boundary=cross_boundary
        self.STAs=[]
        self.raw_type=raw_type
        self.status="Not yet start"  #--this slot have not started yet
        # "Idle"--no station is reporting in this slot;
        # "Collision"--someone is reporting but nothing is correctly decoded
        # "Received"--someone is reporting and the report is correctly decoded

    def register_STA(self,STA):
    # This function is called when some STAs is added into this group to wakes up at this slot
    # Input:
    #   STAs--the STA that is registered in this slot
    # Output:
    #   The current registered STAs in this slot
        self.STAs.append(STA)
        return self.STAs

class RAW():
    def __init__(self,raw_type,paged_only): # we do not consider the RA frame right now
        self.start_time,self.duration=None,None
        self.paged_only=paged_only # if only paged STA can access this window
        self.paged_STAs,self.STAs=[],[]
        self.slot_list=[]
        self.raw_type=raw_type # General or Trigger

    def parameter_setting(self,start_time,duration,slot_amount,STA_list,AID_min=0,AID_max=0):
    # This function is called when we need to set the parameter of this RAW
    # This function must be called when STAs are already registered
    # Input:
    #   start_time--the start time of this raw
    #   duration--how long will this raw last
    #   paged_only--if the raw is only restricted to the paged STA
    #   slot_amount--the number of slot_list this raw has
        self.start_time,self.duration=start_time,duration
        self.end_time=self.start_time+self.duration
        # self.paged_only=paged_only
        self.slot_amount=slot_amount
        self.AID_min,self.AID_max=AID_min,AID_max
        if self.paged_only:
            assert self.paged_STAs, "RAW is paged only but no STA is paged"
            self.STAs=self.paged_STAs
        else:
            self.STAs=[x for x in STA_list if (x.AID<=self.AID_max and x.AID>=self.AID_min)]
        self.STAs.sort(key=lambda x:x.AID)
        self.__slot_division__()

    def page_STA(self,STA):
    # This function is called to page a STA in this RAW
    # Input:
    #   STA--the STA to be paged in this RAW
    # Output:
    #   The list of STAs has been paged--if the STA is successfully paged
    #   Fales--otherwise
        if not STA in self.paged_STAs: # the paged STA must be involved in this RAW
            self.paged_STAs.append(STA)
            self.paged_STAs.sort(key=lambda x:x.AID)
            return self.paged_STAs
        else:
            return False

    def __slot_division__(self):
    # This function is to further divide the RAW duration into slot
        assert not self.paged_only or self.page_STA, 'RAW is paged only but no STA is paged'
        for i in range(self.slot_amount): # divide the RAW duration into slot_list
            start_time=self.start_time+self.duration/self.slot_amount*i
            end_time=start_time+self.duration/self.slot_amount
            self.slot_list.append(RawSlot(start_time,end_time,raw_type=self.raw_type))
        import random
        offset=random.randint(0,9000)
        if self.paged_only==False:# allocate the STAs into slot_list according to its AID
            for each in self.STAs: # choose a slot to join
                slot_index=(each.AID+offset) % self.slot_amount
                self.slot_list[slot_index].register_STA(each)
        else: # allocate the STAs into slot_list according to its relative locations in the paged bits
            for i in range(self.paged_STAs.__len__()):
                slot_index=(i+offset) % self.slot_amount
                self.slot_list[slot_index].register_STA(self.paged_STAs[i])

class RAW_for_blocks(RAW):
    def __init__(self):
        super().__init__("General",False)

    def parameter_setting(self,start_time,duration,block,STA_list):
    # This function is to set the check raw paramenters
    # Input:
    #   start_time--the start time of this raw
    #   duration--how long will this raw last
    #   block--the STA block that need to be checked
    #   STA_list--all the STAs associated with AP
        self.block=block
        AID_max=max(x.AID for x in block.STA_list)
        AID_min=min(x.AID for x in block.STA_list)
        super().parameter_setting(start_time,duration,1,STA_list,AID_min,AID_max)
        

class PollingRound():
    # This class is for a time duration called polling round, each polling round consists of 
    # a beacon broadcasting and several RAW periods
    def __init__(self,timer,max_data_size,AP,STA_list):
        import packet
        temp=timer.slot_time*15+timer.DIFS+timer.SIFS+packet.Packet(timer,'NDP ACK').transmission_delay()+1
        self.trigger_slot_duration=temp+packet.Packet(timer,'NDP Ps-poll').transmission_delay()
        self.data_slot_duration=temp+packet.Packet(timer,'Data',size=max_data_size).transmission_delay()
        self.timer=timer
        self.AP,self.STA_list=AP,STA_list
        self.current_RAW_slot=None

    def set_polling_target(self,STAs_to_check,STAs_to_poll,blocks_to_check):
    # This function is called to define the which STAs need to be checked be polled and which blocks need to be checked.
    # Input:
    #   STAs_to_check--the STAs that need to be checked whether they have alarm report through trigger frame
    #   STAs_to_poll--the STAs that has alarm report need to send (which is check in former round)
    #   blocks_to_check--the blocks that need to be checked whether it is affected by this event
        self.STAs_to_check=STAs_to_check
        self.STAs_to_poll=STAs_to_poll
        self.blocks_to_check=blocks_to_check

    def generate_beacon(self,beacon_announce_time,channel_status,max_data_size):
    # This function is called to generate the RAWs according to the STAs need to check whether they have alarm report,
    # the STAs need to collect their alarm report (i.e., these STAs have checked and the AP find they have alarm report)
    # and the blocks that need to be check whether they are affected by the event
    # Input:
    #   beacon_announce_time--when will the beacon be announced
    # Output:
    #   beacon--the result beacon frames need to be announced.
        import packet
        self.trigger_RAWs,self.collect_RAWs,self.check_RAWs=[],[],[]
        if self.STAs_to_check: # construct Trigger RAWs to check if each STA has the alarm report
            new_RAW=RAW("Trigger",True)
            for each_STA in self.STAs_to_check: # page all the STAs invovled
                new_RAW.page_STA(each_STA)
            self.trigger_RAWs.append(new_RAW)

        if self.STAs_to_poll: #construct General RAWs to collect the data from STAs
            new_RAW=RAW("General",True)
            for each_STA in self.STAs_to_poll:
                new_RAW.page_STA(each_STA)
            self.collect_RAWs.append(new_RAW)
            
        if self.blocks_to_check: #construct General RAWs to check if alarm report exist in this block
            for each_block in self.blocks_to_check:
                new_RAW=RAW_for_blocks()
                self.check_RAWs.append(new_RAW)
        self.RAWs=self.trigger_RAWs+self.collect_RAWs+self.check_RAWs
        # set the parameters of all the raws in this polling round
        beacon=packet.BeaconFrame(self.RAWs,self.timer,self.AP,self.STA_list)
        if channel_status=="Busy": # need multiple beacon frame to ensure the beacon is correctly received
            import math
            transmission_finish_time=packet.Packet(self.timer,"Data",size=max_data_size).transmission_delay()
            duration_for_beacon=self.timer.SIFS+beacon.transmission_delay()
            number_of_beacons=math.ceil(transmission_finish_time/duration_for_beacon)+1
            start_time=number_of_beacons*duration_for_beacon+beacon_announce_time+1-self.timer.SIFS
        else:   
            start_time=beacon_announce_time+beacon.transmission_delay()+1

        if self.trigger_RAWs:
            self.trigger_RAWs[0].parameter_setting(start_time,self.trigger_slot_duration*self.STAs_to_check.__len__(),
                self.STAs_to_check.__len__(),self.STA_list) # set the parameters of the trigger RAW
            start_time=self.trigger_RAWs[0].end_time
        if self.collect_RAWs:
            self.collect_RAWs[0].parameter_setting(start_time,self.data_slot_duration*self.STAs_to_poll.__len__(),
                self.STAs_to_poll.__len__(),self.STA_list)  # set the parameters of the collect RAW
            start_time=self.collect_RAWs[0].end_time
        for i in range(self.blocks_to_check.__len__()): 
            block=self.blocks_to_check[i]
            self.check_RAWs[i].parameter_setting(start_time,self.data_slot_duration,block,self.STA_list) 
            # set the parameters of check RAW
            start_time=self.check_RAWs[i].end_time

        self.end_time=max(x.end_time for x in beacon.RAWs)
        if channel_status=="Busy":
            return [beacon]*number_of_beacons
        else:
            return [beacon]

    def find_current_slot(self,current_time):
    # This function is called when a raw slot start, we need to identify which raw slot it is
    # Input:
    #   current_time--the start time of this raw slot
    # Output:
    #   self.current_RAW_slot--the slot which is currently conducted
        for each_RAW in self.RAWs:
            for each_slot in each_RAW.slot_list:
                if each_slot.start_time==current_time:
                    self.current_RAW_slot=each_slot
                    return self.current_RAW_slot


    def polling_round_analyse(self):
    # This function is called when a polling round ends, we need to know in the next round what we need to do
    # Output
    #   next_STAs_to_check--the STAs to be checked in next polling round
    #   next_STAs_to_collect--the STAs to be polled in next pollling round
    #   next_blocks_to_check--the blocks to be checked in next polling round
        next_STAs_to_collect,next_STAs_to_check,next_blocks_to_check=[],[],[]
        for each_RAW in self.trigger_RAWs:
            for each_slot in each_RAW.slot_list: # check whether the ps-poll is get
                # assert each_slot.status=="Idle" or each_slot.status=="Received", 'a Trigger RAW slot is Collided'
                if each_slot.status=="Received": # collect data from this STA in next round
                    next_STAs_to_collect+=each_slot.STAs
        for each_RAW in self.check_RAWs:
            block=each_RAW.block
            status=each_RAW.slot_list[0].status
            assert status!="Not yet start", "a RAW does not start as rquested"
            if status!="Idle":
                if block.children_blocks: # check the children blocks
                    next_blocks_to_check+=block.children_blocks
                else: # check each STAs in this block
                    next_STAs_to_check+=block.STA_list
        return next_STAs_to_check,next_STAs_to_collect,next_blocks_to_check