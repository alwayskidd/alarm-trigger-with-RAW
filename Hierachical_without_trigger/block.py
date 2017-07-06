class Block:
    ########################################################################################
    # This class represents the STA classifications according to their physical locations
    ########################################################################################
    def __init__(self,block_ID,area,level=0):
        self.STA_list=[]
        self.children_blocks=[] # can have multiple chilren
        self.parent_block=None # can only have one child
        self.level=int(level)
        self.ID=block_ID
        self.area=area # [top,bottom,left,right]
        [self.top,self.bottom,self.left,self.right]=area
        self.STA_received,self.block_finished=[],False # the polling situation of a STA and a block
        self.block_check=None # could be True if the block has alarm report, or False if the block has no alarm report
        # if the alarm report from this STA is received then this STA is regarded as being polled
        # if all the STAs in the block are being polled then the block is regarded as being polled

    def report_received(self,STA):
    # This function is called when a alarm report is received, or AP has polled this STA
    # This function is to remark the STA as a polled STA
    # Input:
    #   STA--the source of the alarm report
    # Output:
    #   True--all STAs in this block are polled; False--otherwise
        assert STA in self.STA_list, "recieved an alarm from STA not in this block"
        # assert not STA in self.STA_polled, "received an alarm from STA which have already reported"
        if not STA in self.STA_received:
            self.STA_received.append(STA)
        if len(set(self.STA_list))==len(set(self.STA_received)): # remark this block as a polled block
            self.block_finished=True
        return self.block_finished

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

class BlockList():
    def __init__(self):
        self.STA_received=[]
        self.blocks=[]
        self.min_length=125

    def add_block(self,block):
    # add a block into this list
    # Output:
    #   True--the block is added
    #   False--the block is not added due to 1. size is too small 2. has already be included
        if (not block in self.blocks and abs(block.area[0]-block.area[1])>=self.min_length):
            self.blocks.append(block)
            self.blocks=sorted(self.blocks, key=lambda block:block.level)
            return True
        return False

    def block_relationship_construct(self):
    #   build the tree structure of the block
        for block_x in self.blocks:
            for block_y in self.blocks: # construct the parent-children relationships
                if (block_x!=block_y and block_y.level-1==block_x.level and block_y.right<=block_x.right and 
                    block_y.left>=block_x.left and block_y.top<=block_x.top and block_y.bottom>=block_x.bottom
                    and not block_y in block_x.children_blocks): # block_y is within the area of block_x
                    block_y.parent_block=block_x
                    block_x.children_blocks.append(block_y)

    def find_sensors_block(self,sensor,level=None):
    # Find the block a sensor belongs to. (All the block levels)
    # Input:
    #   sensor--the sensor that need to find its corresponding blocks
    # Output:
    #   located_blocks--the blocks that contains this sensor
        located_blocks=[]
        for each_block in self.blocks:
            if sensor in each_block.STA_list:
                located_blocks.append(each_block)
        located_blocks=sorted(located_blocks, key=lambda block:block.level)
        if level==None:
            return located_blocks
        else:
            return [x for x in located_blocks if x.level==level]

    def find_neighbours(self,block,level=None):
    # Find a block's neighbours whose block level is given by arg "level"
    # Input:
    #   block--the block need to find its neighbour blocks
    #   level--the neighbour blocks' level
    # Output:
    #   neighbours--the blocks that attached to this block
        neighbours=[]
        if level==None: # no level is indicated, then the neighbours should be at the same level as the current block
            level=block.level
        for each_block in self.blocks:
            if each_block.level==level and each_block!=block:
                intersect_top=min(each_block.top,block.top)
                intersect_bottom=max(each_block.bottom,block.bottom)
                intersect_right=min(each_block.right,block.right)
                intersect_left=max(each_block.left,block.left)
                if intersect_top>=intersect_bottom and intersect_right>=intersect_left: # has at least one point intersect of this two blocks
                    neighbours.append(each_block)
        return(neighbours)

    def report_received(self,packet):
    # This function is called when an alarm report is received, or AP polled this STA
    # This function is used to remark the source of the alarm report in its blocks as polled
    # Input:
    #   STA--the STA that has been polled
        STA=packet.source
        assert not STA in self.STA_received, "A frame is received multiple times"
        self.STA_received.append(STA)
        for each_block in self.blocks:
            if STA in each_block.STA_list:
                each_block.report_received(STA)

    def get_blocks_at_certain_level(self,level):
        return [block for block in self.blocks if block.level==level]


    def print_blocks_information(self):
        blocks=[x for x in self.blocks if x.STA_received]
        print("There are totally "+str(blocks.__len__())+" blocks")
        for each_block in blocks:
            print(each_block.children_blocks.__len__())
            print(vars(each_block))