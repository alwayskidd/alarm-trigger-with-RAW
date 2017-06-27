class channel():
    def __init__(self):
        import copy
        self.maximum_hearing_distance=150
        self.STA_transmission_power=23 #dBm
        self.AP_transmission_power=0
        self.AP_antena=6 #dBi
        self.STA_antena=0 #dB
        self.minimum_hearing_power=-98 #dBm
        self.minimum_interference_power=-105 #dBm
        self.transmission_STA_list=[]
        self.packet_list=[]

    def register_devices(self,device_list):
        self.device_list=sorted(device_list, key=lambda x:x.AID, reverse=True)

    def rx_power_at_STA(self,STA1,STA2):
	#This function is used to calculate the receiving power at STA2 when STA1 is transmitting
	# Input:
	#	STA1--the transmitter
	#	STA2--the receiver/listenner
	# Output:
	#	rx_power--the receiving power at STA2 in dBm
        import math,AP
        x1,y1,x2,y2=STA1.x,STA1.y,STA2.x,STA2.y
        distance=math.sqrt((x1-x2)**2+(y1-y2)**2)
        if distance==0:
            return 10
        if isinstance(STA1,AP.AP) or isinstance(STA2,AP.AP): # use the STA to AP channel model
            rx_power=self.STA_transmission_power-(8+37.6*math.log10(distance))+self.STA_antena+self.AP_antena
        else: # use the STA to STA channel model
            rx_power=self.STA_transmission_power-(-6.17+58.6*math.log10(distance))+self.STA_antena
        return rx_power  # dBm

    def __update_receiving_power__(self): 
    # update the receiving power at STA while there is pacekt join or leave the channel
        for each_device in self.device_list:
            each_device.update_receiving_power(self.packet_list)

    def register_transmission_in_air(self,new_packets): 
	# This function is called when there is a new packet start its transmission in the air
	# Input:
        #	new_packet--the newly transmitted packet
        import math
        for each_packet in new_packets:
            self.packet_list.append(each_packet)
            self.transmission_STA_list.append(each_packet.source)
        print("There are currently "+str(self.packet_list.__len__())+" STAs are transmitting:"+
            str([x.AID for x in self.transmission_STA_list]))
        self.__update_receiving_power__()
        for each_packet in new_packets:
            for each_device in self.device_list: # update the packet that can be received
                each_device.update_packet_can_receive(each_packet)

    def clear_transmission_in_air(self,packet): 
    # This function is called when a packet has finished its transmission
    # Input:
    #	packet--the packet that finished its transmission
        print("A packet from STA "+str(packet.source.AID)+" has finished its transmission")
        import math
        self.packet_list.remove(packet)
        self.transmission_STA_list.remove(packet.source)
        print("There are currently "+str(self.packet_list.__len__())+" STAs are transmitting:"+
            str([x.AID for x in self.transmission_STA_list]))
        self.__update_receiving_power__()
