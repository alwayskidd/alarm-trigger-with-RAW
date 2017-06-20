import event,random
class Device:
    def __init__(self,locations,CWmin,CWmax,timer,channel):
        self.channel,self.timer=channel,timer # system timer and system channel
        self.x,self.y=locations[0],locations[1] # the location of this device
        self.CWmin,self.CWmax=CWmin,CWmax
        self.backoff_stage=CWmin
        self.backoff_timer=random.randint(0,self.backoff_stage-1)
        self.queue=[] # data queue
        self.receiving_power=0
        self.status="Sleep" #the status of this device, "Sleep","Transmit","Listen"
        self.channel_state,self.backoff_status="Idle","Off"
        self.packet_to_send=None
        self.packet_in_air,self.packet_can_receive,self.time_out_event=None,None,None
        self.IFS_expire_event,self.NAV_expire_event=None,None
        self.minimum_interference_power=-105 #dBm
        self.minimum_hearing_power=-98 #dBm
        self.AID=None

    def transmit_packet(self,packet):
    #This function is called when a packet needs to be sent immediately
    #Input: packet--the packet need to be sent
        print("A frame is transmitted into the air from device "+str(self.AID))
        self.channel.register_transmission_in_air(packet)
        self.packet_in_air=packet
        # Let the timer know when the packet transmission will be ended.
        new_event=event.Event("transmission end",self.timer.current_time+packet.transmission_delay())
        new_event.register_device(self)
        self.timer.register_event(new_event)
        self.status="Trasmit"
        return True

    def update_receiving_power(self,packets_in_air):
    #This function is called when the power level in the channel has been changed
    #The channel status will be changed if the power level reaches the minimum interference power
    #Input: 
    #   packets_in_air-- the list of packets that are transmitting in the air
    #Output:
    #   True--the channel status is changed
    #   False--the channel status is not changed
        self.receiving_power=0
        for each in packets_in_air:
            if each.source!=self: # add the receiving power at the attena
                self.receiving_power+=10**(self.channel.rx_power_at_STA(each.source,self)/10)
        # print("update receiving power:"+str(self.receiving_power))

        if self.receiving_power>=10**(self.minimum_interference_power/10) and self.channel_state=="Idle":
        # change the sensed channel status to Busy in this device
            self.channel_state="Busy"
            self.backoff_status="Off" # backoff is interrupted
            if self.IFS_expire_event!=None: # IFS may be interrupted since channel get busy
                if (self.packet_to_send==None or (self.packet_to_send.packet_type!="CTS")
                    and self.packet_to_send.packet_type!="ACK"):
            # The intrruption will be ignored when the pending packet is ACK or CTS frame
                    assert self.IFS_expire_event.time>=self.timer.current_time
                    self.timer.remove_event(self.IFS_expire_event)
                    self.IFS_expire_event=None
                    self.packet_to_send=None
            return True

        if self.receiving_power<10**(self.minimum_interference_power/10) and self.channel_state=="Busy":
        # change the sensed channel status to Idle in this device
            self.channel_state="Idle"
            if self.status=="Listen" and self.time_out_event==None: 
                if ((self.NAV_expire_event==None or 
                self.NAV_expire_event.time<=self.timer.current_time+self.timer.EIFS) and
                self.packet_can_receive==None): #wait until EIFS expire, otherwise wait for the NAV expire
                    # assert self.IFS_expire_event==None, str(self)
                    if self.NAV_expire_event!=None: # remove this event from the timer
                        self.timer.remove_event(self.NAV_expire_event)
                        self.NAV_expire_event=None
                    if self.IFS_expire_event==None: # since AP's SIFS will not be interrupted so there may still be IFS there
                        # assert self.IFS_expire_event==None
                        new_event=event.Event("IFS expire",self.timer.current_time+self.timer.EIFS) #EIFS
                        new_event.register_device(self)
                        self.timer.register_event(new_event) # The EIFS expire event may be replaced by DIFS if the packet can be decoded
                        self.IFS_expire_event=new_event
            return True
        return False

    def update_packet_can_receive(self,new_packet):
    #This function is called when there is a new packet join the network
    #This function must be called after the receiving power is updated
    #Input:
    #   new_packet: The newest joined packet in the air.
        import math
        if new_packet.source==self:
            return False
        if self.status!="Listen": # no packet can be received while STA is not listen
            self.packet_can_receive=None
            return False
        if self.packet_can_receive!=None: # exist a packet that can be corretly decoded, we need to judge if it can still be decoded
            signal_power=self.channel.rx_power_at_STA(self.packet_can_receive.source,self)
            signal_power=10**(signal_power/10)
            interference_power=self.receiving_power-signal_power
            SINR=10*math.log10(signal_power/interference_power)
            if SINR<5: #dB the current packet is interfered that cannot be decoded any longer
                self.packet_can_receive=None
            else: # this packet can still be decoded, i.e., the new joined packet cannot be decoded.
                return False
        # To check whether the new packet can be decoded.
        signal_power=self.channel.rx_power_at_STA(new_packet.source,self)
        if signal_power<self.minimum_hearing_power: # the packet cannot be received
            return False
        signal_power=10**(signal_power/10)
        interference_power=self.receiving_power-signal_power
        if interference_power==0: # this packet can be correctly decoded
            self.packet_can_receive=new_packet
            return True
        SINR=10*math.log10(signal_power/interference_power)
        if SINR>=5: #dB
            self.packet_can_receive=new_packet
            return True
        else:
            return False