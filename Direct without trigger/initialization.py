import system_timer,sensor,event,channel,AP,block
import statistics_collection,random,math,os

def init(amount,d_max,timer,RTS_enable,suspend_enable,CWmax,channel,threshold=0.7,detection_time=300*10**3,data_size=100):
    CWmin=16
    file=open(os.path.pardir+"/events/station_list_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","rb")
    import pickle
    amount=pickle.load(file)
    system_AP=AP.AP([0,0],CWmin,CWmax,timer,channel,threshold,detection_time)
    STA_list=[]
    for i in range(amount): # generate sensors according to the recorded locations
        x=pickle.load(file)
        y=pickle.load(file)
        STA_list.append(sensor.Sensor(i+1,CWmin,CWmax,[x,y],RTS_enable,suspend_enable,system_AP,timer,channel,data_size))
    file.close()
    system_AP.register_associated_STAs(STA_list)
    file=open(os.path.pardir+"/events/packet_events_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","rb")
    amount=pickle.load(file)
    print("there are "+str(amount)+" packet there")
    for i in range(amount): # load event from the corresponding file
        start_time=pickle.load(file)
        AID=pickle.load(file)
        assert STA_list[AID-1].AID==AID
        new_event=event.Event("packet arrival",start_time)
        new_event.register_device(STA_list[AID-1])
            # event=pickle.load(file)
        timer.register_event(new_event)
        statistics_collection.collector.register_packet_generated()
    file.close()
    system_AP.STA_list=STA_list
    print("STA amount is "+str(STA_list.__len__()))
    return(system_AP,STA_list)

def AID_assignment(STA_list,radius=1000):
    import math
    block_list=block.BlockList()
    search_areas=[]
    search_areas.append([radius,0,-radius,0]) #top,bottom,left,right
    search_areas.append([radius,0,0,radius])
    search_areas.append([0,-radius,-radius,0])
    search_areas.append([0,-radius,0,radius])
    block_ID=0
    AID=1
    while search_areas: # assign AIDs
        area=search_areas.pop(0)
        [top,bottom,left,right]=area
        new_block=block.Block(block_ID,area,level=math.log2(radius//(top-bottom)))
        for each_STA in STA_list:
            if each_STA.x<right and each_STA.x>=left and each_STA.y<top and each_STA.y>=bottom: #
                new_block.add_STA(each_STA)
        if new_block.STA_list:
            block_list.add_block(new_block)
            block_ID+=1
            if new_block.STA_list.__len__()==1: # assign the lowest AID to this node
                new_block.STA_list[0].AID=AID
                AID+=1
            else: # further divide this area into four pieces
                center_x=(left+right)/2
                center_y=(top+bottom)/2
                search_areas.insert(0,[top,center_y,left,center_x])
                search_areas.insert(1,[top,center_y,center_x,right])
                search_areas.insert(2,[center_y,bottom,left,center_x])
                search_areas.insert(3,[center_y,bottom,center_x,right])
    # import time
    block_list.block_relationship_construct()
    block_list.print_blocks_information()
    return block_list