class RawSlot():
    """docstring for raw_slot"""
    def __init__(self,start_time,end_time,raw_type="General",cross_boundary=False):
        self.start_time=start_time
        self.end_time=end_time
        self.cross_boundary=cross_boundary
        self.STAs=[]
        self.type=raw_type

    def register_STA(self,STA):
    # This function is called when some STAs is added into this group to wakes up at this slot
    # Input:
    #   STAs--the STA that is registered in this slot
    # Output:
    #   The current registered STAs in this slot
        self.STAs.append(STA)
        return self.STAs

class RAW():
    def __init__(self,start_time,end_time,paged_only,slot_amount,raw_type,CW_min=7,CW_max=15): # we do not consider the RA frame right now
        self.start_time,self.end_time=start_time,end_time
        self.paged_only=paged_only # if only paged STA can access this window
        self.STAs,self.paged_STAs=[],[]
        self.slots=[]
        self.RAW_CW_min=CW_min
        self.RAW_CW_max=CW_max
        self.raw_type=raw_type

    def register_STA(self,group_start_AID,group_end_AID,STA_list):
    # This function is called to register STAs in this RAW
    # In each RAW, the STAs that can access the channel in this RAW is the STAs with start_AID<=STA<=end_AID
    # Input:
    #   group_start_AID--the smallest AID that the group of STAs will have
    #   group_end_AID--the largest AID that the group of STAs will have
    #   STA_list--the list of all STAs associated with AP
    # Output:
    #   The list of STAs that will involved in this RAW
        for each in STA_list:
            if each.AID>=group_start_AID and each.AID<=group_end_AID:
                self.STAs.append(each)
        self.STAs.sort(key=lambda x:x.AID, reserve=False)
        return self.STAs

    def page_STA(self,STA):
    # This function is called to page a STA in this RAW
    # Input:
    #   STA--the STA to be paged in this RAW
    # Output:
    #   The list of STAs has been paged--if the STA is successfully paged
    #   Fales--otherwise
        if STA in self.STAs: # the paged STA must be involved in this RAW
            self.paged_STAs.append(STA)
            self.paged_STAs.sort(key=lambda x:x.AID, reserve=False)
            return self.paged_STAs
        else:
            return False

    def slot_division(self,slot_amount):
    # This function is to further divide the RAW duaration into slot
    # Input:
    #   slot_amount--the number of slot
        for i in range(slot_amount): # divide the RAW duaration into slots
            RAW_duration=self.end_time-self.start_time
            start_time=self.start_time+RAW_duration/slot_amount*i
            end_time=start_time+RAW_duration/slot_amount
            self.slots.append(RawSlot(start_time,end_time,raw_type=self.raw_type))
        import random
        offset=random.randint(9000)
        if self.paged_only==False:# allocate the STAs into slots according to its AID
            for each in self.STAs: # choose a slot to join
                slot_index=(each.AID+offset) % slot_amount
                self.slots[slot_index].register_STA(each)
        else: # allocate the STAs into slots according to its relative locations in the paged bits
            for i in range(self.paged_STAs.__len__()):
                slot_index=(i+offset) % slot_amount
                self.slots[slot_index].register_STA(self.paged_STAs[i])