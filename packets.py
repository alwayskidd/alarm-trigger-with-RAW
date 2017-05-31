class packets:
	def __init__(self,timer,packet_type,source,destination):
		self.registered_time=timer.current_time
		self.delay=0
		self.status="S" # succeed or failure S or F
		self.STA=source
		self.packet_type=packet_type
		if packet_type=="data":
			self.size=20
			self.NAV=timer.SIFS+packets(timer,"ACK",source,destination).transmission_delay()
		elif packet_type=="RTS":
			self.size=20
			self.NAV=timer.SIFS+packets(timer,"CTS",source,destination).transmission_delay()+timer.SIFS+packets(timer,"data",source,destination).transmission_delay()+timer.SIFS+packets(timer,"ACK",source,destination).transmission_delay() # SIFS*3+CTS+DATA+ACK
		elif packet_type=="CTS":
			self.size=14
			self.NAV=timer.SIFS+packets(timer,"data",source,destination).transmission_delay()+timer.SIFS+packets(timer,"ACK",source,destination).transmission_delay() 
		elif packet_type=="ACK":
			self.size=750 #14*40 # us
			self.NAV=0
		self.source=source # an AP or an STA
		self.destination=destination #should be list of STAs or AP
		self.NAV_affect_list=[]

	def cal_delay(self,time):
		return(time-self.registered_time)

	def transmission_delay(self,phy_data_rate=150):
		if self.packet_type!="ACK":
			return(self.size*8/phy_data_rate*1000)
		return(self.size)

	def register_NAV_affect_STA(self,STA):
		#print("register NAV are called "+str(self))
		self.NAV_affect_list.append(STA)