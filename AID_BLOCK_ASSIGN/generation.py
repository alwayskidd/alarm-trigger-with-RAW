import sensor,packets,AP,event
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