from matplotlib.patches import Ellipse,Circle
import matplotlib.pyplot as plt

for d_max in range(400,2001,300):
	fig=plt.figure()
	ax=fig.add_subplot(111)
	file=open("station_list_amount=500_d_max="+str(d_max)+".pkl","rb")
	import pickle
	amount=pickle.load(file)
	STA_list=[]
	file_out=open("station_list.txt","w+")
	for i in range(amount):
		x=pickle.load(file)
		y=pickle.load(file)
		STA_list.append([x,y])
		file_out.write("STA "+(str(i))+"'s location: "+str([x,y])+"\n")

	file.close()

	file=open("packet_events_amount=500_d_max="+str(d_max)+".pkl","rb")
	amount=pickle.load(file)
	packets=[]
	file_out=open("packet_events_amount=500_d_max="+str(d_max)+".txt","w+")

	print(amount)
	temp=[]
	for i in range(amount):
		start_time=pickle.load(file)
		AID=pickle.load(file)
		packets.append(AID-1)
		temp.append([start_time,AID])

	temp.sort()
	print(temp)

	for i in range(amount):
		[start_time,AID]=temp[i]
		file_out.write("STA "+str(AID).ljust(5)+" location is "+str(STA_list[AID-1]).ljust(42)+" is triggered at time "+str(start_time)+"\n")

	file.close()
	file_out.close()

	for i in range(STA_list.__len__()):
		[x,y]=STA_list[i]
		if i in packets:
			ax.plot(x,y,'ro')
		else:
			ax.plot(x,y,'bo')

	cir=Circle(xy=(0.0,0.0),radius=1000,fill=False)
	ax.add_patch(cir)
	plt.axis('scaled')
	plt.axis('equal')
	plt.savefig("amount=500_d_max="+str(d_max)+".png")