import time
class AlarmDetector():
    def __init__(self,timer,maximum_busy_allowed):
        self.timer,self.maximum_busy_allowed=timer,maximum_busy_allowed # in ms
        self.current_state="Idle" # could be idle or busy
        self.detect_start_time=self.timer.current_time # record the detect time
        self.frame_receiving_duration=0 # the accumulated duration for receiving a packet that can be correctly decoded
        self.idle_duration=0 # the accumulated duration for listening the channel but no one is sending
        self.idle_start_time=0 # the time when current idle state starts
        self.on_off="On"

        # self.busy_duration,self.busy_start_time=None,None
        # self.idle_duration,self.idle_start_time=None,None
        # self.last_ACK_transmitted,self.last_ACK_time=False,None

    def turn_off(self):
        self.on_off="Off"
    def turn_on(self):
        self.on_off="On"

    def reset(self):
    # This function is called to reset the attributes in this class
        self.detect_start_time=self.timer.current_time
        self.frame_receiving_duration=0
        self.idle_duration,self.busy_duration=0,0
        if self.current_state=="Idle":
            self.idle_start_time=self.timer.current_time
        else:
            self.idle_start_time=None

    def channel_busy(self):
    # This function is called when channel is detect as busy
    # Output:
    #   True--alarm is detected
    #   False--no alarm is detected
        if self.on_off=="On":
            if self.current_state=="Idle":
                assert self.idle_start_time!=None, "channel changed from busy to idle but there is no idle record"
                self.idle_duration+=self.timer.current_time-self.idle_start_time # accumulate the idle time
                self.current_state="Busy"
            self.busy_duration=(self.timer.current_time-self.detect_start_time-
                self.idle_duration-self.frame_receiving_duration)
            flag=self.detect_alarm()
            self.idle_start_time=None
            return flag
        else:
            return False

    def channel_idle(self):
    # This function is called when channel is detect as idle
    # Output:
    #   True--alarm is detected
    #   False--no alarm is detected
        if self.on_off=="On":
            if self.current_state=="Busy":
                self.current_state="Idle"
                # self.idle_start_time=self.timer.current_time
            else:
                if self.idle_start_time!=None: # update the idle duration
                    self.idle_duration+=self.timer.current_time-self.idle_start_time
            self.idle_start_time=self.timer.current_time
            # print(self.frame_receiving_duration)
            self.busy_duration=(self.timer.current_time-self.detect_start_time-
                self.idle_duration-self.frame_receiving_duration)
            return self.detect_alarm()
        else:
            return False

    def frame_received(self,frame):
    # This function si called when a alarm report is received by AP
    # Input:
    #   frame--the received frame
    # Output:
    #   True--alarm is detected
    #   False--no alarm is detected
        if self.on_off=="On":
            self.frame_receiving_duration+=frame.transmission_delay()
            self.busy_duration=(self.timer.current_time-self.detect_start_time-
                self.idle_duration-self.frame_receiving_duration)
            return self.detect_alarm()
        else:
            return False


    def detect_alarm(self):
        if self.busy_duration==0: # we can reset the alarm detector
            self.reset()
            print("detector reset due to no busy time")
            return False
        if self.idle_start_time!=None:
            current_idle_duration=self.timer.current_time-self.idle_start_time
            if current_idle_duration>1024*self.timer.slot_time:
                self.reset()
                print("detector reset due to long idle preriod")
                return False
        if self.idle_duration*5>self.timer.current_time-self.detect_start_time:
            self.reset()
            print("detector reset due to high proportion of idle period")
            return False
        if self.frame_receiving_duration*5>self.busy_duration:
            print(self.frame_receiving_duration*5>self.busy_duration)
            print("receiving:"+str(self.frame_receiving_duration))
            print("busy:"+str(self.busy_duration))
            self.reset()
            print("detector reset due to high proportion of receiveing period")
            return False
        if self.busy_duration>=self.maximum_busy_allowed:
            print("alarm detected at "+str(self.timer.current_time))
            time.sleep(10)
            # exit(0)
            return True
        else:
            return False