import sensor,packet,AP,event

def packet_generation(STA_list,location,speed,sp_type,arg): #generate packe according to the alarm spreading model
# speed should be in unit of m/s
	import math,random
	assert sp_type=="All" or sp_type=="Exp" or sp_type=="Sq"
	packet_generation_events=[]
	counter=0
	x=location[0]
	y=location[1]
	for each in STA_list: #calculate the packet arrival time
		#print(each.AID)
		distance=math.sqrt((each.x-x)**2+(each.y-y)**2)

		if sp_type=="All":
			new_event=event.event("packet arrival",start_time=(distance/speed*10**6))
			new_event.register_STA(each)
			packet_generation_events.append(new_event)
			counter+=1
			# timer.register_event(new_event)

		if sp_type=="Exp":
			a=arg
			probability=math.exp(-a*distance)
			if random.random()<=probability:
				new_event=event.event("packet arrival",start_time=(distance/speed*10**6))
				new_event.register_STA(each)
				packet_generation_events.append(new_event)
				counter+=1
				# timer.register_event(new_event)

		if sp_type=="Sq":
			d_max=arg
			if distance<d_max:
				probability=math.sqrt(d_max**2-distance**2)
			else:
				probability=0
			if random.random()<=probability:
				new_event=event.event("packet arrival",start_time=(distance/speed*10**6))
				new_event.register_STA(each)
				packet_generation_events.append(new_event)
				counter+=1
	print("packet amount="+str(counter))

	import time
	# time.sleep(1)
	return packet_generation_events,counter


def STA_generation(amount,radius,RTS_enable,CWmin,CWmax,system_AP):
	STA_list=[]
	import math,random
	for i in range(1,amount+1):
		alpha=random.random()*2*math.pi
		r=math.sqrt(random.random())*radius
		x=r*math.cos(alpha)
		y=r*math.sin(alpha)
		STA_list.append(sensor.sensor(i,CWmin,CWmax,[x,y],RTS_enable,False,system_AP))
	return STA_list


radius=1000
RTS_enable=True
CWmin=16
CWmax=16*2^5
import math,random
alpha=random.random()*2*math.pi
r=math.sqrt(random.random())*radius
x=r*math.cos(alpha)
y=r*math.sin(alpha)
print(x,y)


amount=500 # the number of STAs
system_AP=AP.AP([0,0],STA_list=[])
STA_list=STA_generation(amount,radius,RTS_enable,CWmin,CWmax,system_AP)

for d_max in range(400,1601,300): # the radius of the affected area
# amount=100 #amount of STAs
	print(amount,d_max)
	file=open("station_list_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","wb")
	system_AP.STA_list=STA_list
	import pickle
	pickle.dump(amount,file)
	for each in STA_list:
		pickle.dump(each.x,file)
		pickle.dump(each.y,file)
	file.close()

	file=open("packet_events_amount="+str(amount)+"_d_max="+str(d_max)+".pkl","wb")
	[packet_events,packet_amount]=packet_generation(STA_list,[x,y],4000,"Sq",d_max)
	# print(amount)
	pickle.dump(packet_amount,file)
	for each in packet_events:
		pickle.dump(each.time,file)
		pickle.dump(each.STA_list[0].AID,file)
	file.close()