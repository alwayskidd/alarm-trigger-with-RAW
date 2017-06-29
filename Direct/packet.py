class Packet:
	def __init__(self,timer,packet_type,source=None,destination=None,size=None):
		self.registered_time=timer.current_time
		self.delay=0
		self.status="S" # succeed or failure S or F
		self.STA=source
		self.packet_type=packet_type
		if packet_type=="Data":
			if size==None:
				self.size=40 # bytes
			else:
				self.size=size #bytes
			self.NAV=timer.SIFS+Packet(timer,"NDP ACK",source,destination).transmission_delay()
		elif packet_type=="RTS":
			self.size=20 # bytes
			self.NAV=(timer.SIFS+Packet(timer,"CTS",source,destination).transmission_delay()+
				timer.SIFS+Packet(timer,"data",source,destination).transmission_delay()
			+timer.SIFS+packets(timer,"NDP ACK",source,destination).transmission_delay()) # SIFS*3+CTS+DATA+ACK
		elif packet_type=="CTS":
			self.size=14 #bytes
			self.NAV=(timer.SIFS+Packet(timer,"data",source,destination).transmission_delay()+
				timer.SIFS+Packet(timer,"NDP ACK",source,destination).transmission_delay())
		elif 'NDP' in packet_type:
			# print(packet_type)
			self.size=14 #14 symbols
			if packet_type=="NDP Ps-poll":
				self.NAV=(timer.SIFS+Packet(timer,"NDP ACK",source,destination).transmission_delay())
			elif packet_type=="NDP ACK":
				self.NAV=0
		self.source=source # an AP or an STA
		self.destination=destination #should be list of STAs or AP
		self.NAV_affect_list=[]

	def cal_delay(self,time):
		return(time-self.registered_time)

	def transmission_delay(self,phy_data_rate=150):
		if not 'NDP' in self.packet_type: # calculate the transmission delay
			# print(self.packet_type)
			return(self.size*8/phy_data_rate*1000)
		else:
			return 560

	def register_NAV_affect_STA(self,STA):
		#print("register NAV are called "+str(self))
		self.NAV_affect_list.append(STA)

class BeaconFrame(Packet):
	def __init__(self,RAWs,timer,AP,STA_list):
		super().__init__(timer,packet_type='Beacon Frame',source=AP,destination=STA_list)
		size_basic=19 # bytes, without considering the RPS element
		# Frame Control | Duration | SA | Timestamp | Change Sequence | Compressed SSID | Access Network Options | 
		# Frame Body (In this work only has RPS element) | FCS #
		size_RPS_elements=RAWs.__len__()*9 # bytes | Element ID | Length | RAW control | RAW Slot Define | Start TIme | Group |
		self.RAWs=RAWs
		self.size=size_basic+size_RPS_elements