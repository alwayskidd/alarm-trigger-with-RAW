import numpy as np
from scipy import stats
import re

def read_data_True(d_max,amount,CW_max,total_round,suspend):
	direction="./results/d_max="+str(d_max)+"_amount="+str(amount)+"/"
	filename="CWmax="+str(CW_max)+"_suspend="+str(suspend)+"_round="
	packet_received,average_backoffs,total_time=[],[],[]
	for i in range(0,total_round):
		file=open(direction+filename+str(i)+".txt",'r')
		for eachline in file:
			temp=eachline.split(" ")
			l=len(temp)
			if l>=7 and "transmitted" in temp[-1]:
				packet_received.append(int(temp[2]))
			if l>=3 and temp[2]=="#":
				average_backoffs.append(float(temp[5]))
			if l>=3 and temp[1]=="end" and temp[2]=="time":
				total_time.append(float(temp[4])/1000)
	return packet_received,average_backoffs,total_time



def confidence_interval(data,confidence):
	temp=np.array(data)
	mean_value=np.mean(temp)
	se=stats.sem(temp)
	yerr=se*stats.t.ppf((1+confidence)/2,len(temp)-1)
	return (mean_value),[(mean_value-yerr/2),(mean_value+yerr/2)]

d_max,amount,CW_max=1600,500,1024
suspend=False
if suspend==False:
	total_round=5
else:
	total_round=10

confidence=0.95
packet_received,average_backoffs,total_time=read_data_True(d_max,amount,CW_max,total_round,suspend)

print("packet received:"+str(confidence_interval(packet_received,confidence))+"\n")
print("average backoffs"+str(confidence_interval(average_backoffs,confidence))+"\n")
print("total time:"+str(confidence_interval(total_time,confidence))+"\n")