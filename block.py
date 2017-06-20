class Block:
    ########################################################################################
    # This class represents the STA classifications according to their physical locations
    ########################################################################################
    def __init__(self,block_ID,area,sub_blocks=[],level=0):
        self.STA_list=[]
        self.sub_blocks=sub_blocks
        self.level=int(level)
        self.ID=block_ID
        self.area=area # [top,bottom,left,right]
        # print(self.STA_list.__len__())
        # self.calculate_AID_range()

    def add_STA(self,STA):
        self.STA_list.append(STA)

    def delete_STA(self,STA):
        assert STA in self.STA_list, "the STA does not belong to current block"
        self.STA_list.remove(STA)

    def calculate_AID_range(self):
        AIDs=[]
        for each in self.STA_list:
            AIDs.append(each.AID)
        print(AIDs)