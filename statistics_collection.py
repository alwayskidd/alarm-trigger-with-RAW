import statistics
class statisticsCollection():
	"""docstring for statistics_collection"""
	def __init__(self):
		self.delays=[]
		# self.contention_level=[]
		self.number_of_packet=0
		self.number_of_assignment=0
		self.successful_transmissions=[]
		self.collisions=0
		self.channel_busy_time=0
		self.last_time_idle=0
		# self.suspension=[]
		self.end_time=0
		self.back_off_stage=[]
		self.back_off_collection_time=[]
		self.contention_STAsN=[]
		self.average_backoffs=[]

	def register_backoff_times(self,attempts,total_backoffs):
		self.average_backoffs.append(total_backoffs/attempts)

	def backoff_stage_collect(self,stage,time,contention_STAsN):
		self.back_off_stage.append(stage)
		self.back_off_collection_time.append(time)
		self.contention_STAsN.append(contention_STAsN)

	def register_successful_transmission(self,packet,time):
		self.successful_transmissions.append([packet,time])

	def register_collision(self):
		self.collisions+=1

	def delay_register(self,delay):
		self.delays.append(delay)

	def register_packet_generated(self):
		self.number_of_packet+=1
	# def register_suspension(self,STA,time,energy,packet_source):
	# 	self.suspension.append([STA,time,energy,packet_source])
	def print_number_of_successful_transmission(self):
		print("there are "+str(self.successful_transmissions.__len__())+ " packets has been transmitted.")
		print("transmission times are: ")
		for each in self.successful_transmissions:
			print("From STA "+str(each[0].source.AID)+" at "+str(each[1]))

	def print_statistics_of_delays(self):
		print("maximum delay is:"+str(max(self.delays)/1000)+"\n")
		if self.delays.__len__()>1:
			self.file.write("maximum delay is:"+str(max(self.delays)/1000)+"\n")
			self.file.write("minimum delay is:"+str(min(self.delays)/1000)+"\n")
			self.file.write("mean value of the delays:"+str(statistics.mean(self.delays)/1000)+"\n")
			self.file.write("standard deviation:"+str(statistics.stdev(self.delays)/1000)+"\n")
		else:
			self.file.write("standard deviation:"+str(0)+"\n")

	def print_other_statistics(self,end_time,packet_size):
		self.file.write("there are "+str(self.number_of_packet)+" packets need to be transmit.\n")
		self.file.write("there are "+str(self.successful_transmissions.__len__())+ " packets has been transmitted.\n")
		# self.file.write("the average # of backoffs "+str(sum(self.average_backoffs)/self.average_backoffs.__len__())+"\n")
		# self.file.write("transmission times are: \n")
		# for each in self.successful_transmissions:
		# 	self.file.write("From STA "+str(each[0].source.AID)+" at "+str(each[1])+"\n")
		# self.file.write("successful_transmissions:"+str(self.successful_transmissions.__len__())+"\n")
		self.file.write("collisions:"+str(self.collisions)+"\n")
		self.file.write("Throughput:"+str(self.successful_transmissions.__len__()*packet_size*8/(self.end_time/10**6)/10**3)+" kbps"+"\n")
		self.file.write("Transmission successful probability:"+\
			str(self.successful_transmissions.__len__()/(self.successful_transmissions.__len__()+self.collisions))+"\n")
		self.file.write("channel busy time:"+str(self.channel_busy_time)+"\n")
		# self.file.write("There are "+str(self.suspension.__len__())+" packets has been suspended to transmit\n")
		self.file.write("The end time is "+str(self.end_time)+"\n")
		self.file.write("backoff stage is\n"+str(self.back_off_stage)+"\n")
		# self.file.write("Number of contention STAs\n"+str(self.contention_STAsN)+"\n")
		# self.file.write("the collect time is\n"+str(self.back_off_collection_time)+"\n")


		# for each in self.suspension:
		# 	self.file.write("STA "+str(each[0].AID)+" receives an packet from "+ str(each[3].AID)+\
		# 		" the energy is "+str(each[2])+" is suspend at "+str(each[1])+"\n")

	# def contention_level_register(self,number_of_STA):
	# 	self.contention_level.append(number_of_STA)

	def clear(self):
		self.__init__()

	def set_output_file(self,file):
		self.file=file


collector=statisticsCollection()