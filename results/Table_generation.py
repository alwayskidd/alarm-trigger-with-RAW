import numpy as np
from scipy import stats

def end_time_statistics(filename):
    end_time_list=[]
    detection_times_list=[]
    frames_to_send=[]
    frames_transmitted=[]
    for i in range(10): 
        fp=open(filename+"_round="+str(i)+".txt",'r')
        for eachline in fp:
            temp=eachline.split(" ")
            if len(temp)>=4 and temp[0]=="The" and temp[1]=="end" and temp[2]=="time" and temp[3]=="is": #record the end time 
                end_time_list.append(float(temp[4])/1000)
            if len(temp)>=5 and temp[2]=="detects" and temp[3]=="alarm": # record how many times the AP detect alarm traffic
                detection_times_list.append(int(temp[6]))
            if len(temp)>=6 and temp[4]=="has" and temp[5]=="been":
                frames_transmitted.append(int(temp[2]))
            if len(temp)>=6 and temp[4]=="need" and temp[5]=="to":
                frames_to_send.append(int(temp[2]))
    confidence=0.95
    average_end_time=np.mean(end_time_list)
    se=stats.sem(end_time_list)
    yerr=se*stats.t.ppf((1+confidence)/2,len(end_time_list)-1)
    # print(average_end_time,yeer,
    #     np.mean(detection_times_list),np.mean(frames_to_send),np.mean(frames_transmitted))
    return np.mean(frames_to_send),np.mean(frames_transmitted),np.mean(detection_times_list),average_end_time,yerr


out_file_name="results.csv"
fp=open(out_file_name,"w")
fp.write("d_max,threshold,T,scheme,number of STAs triggered,number of frames retrived,alarm detecting times,total time spend, confidence interval\n")
for d_max in range(400,1901,300):
    for Thr in np.arange(0.5,1,0.1):
        for T in np.arange(100.0,500.0+1,50.0):
            fp.write(str(d_max)+","+str(Thr)+","+str(T))
            filename="./Hierachical/Thr="+str(Thr)+"_T="+str(T)+"/d_max="+str(d_max)
            fp.write(",Hierachical,")
            frames_to_send,frames_transmitted,detection_times,end_time,interval=end_time_statistics(filename)
            fp.write(str(frames_to_send)+","+str(frames_transmitted)+","+str(detection_times)+","
                +str(end_time)+","+str(interval)+"\n")

            fp.write(str(d_max)+","+str(Thr)+","+str(T))
            filename="./Direct/Thr="+str(Thr)+"_T="+str(T)+"/d_max="+str(d_max)
            fp.write(",Direct,")
            frames_to_send,frames_transmitted,detection_times,end_time,interval=end_time_statistics(filename)
            fp.write(str(frames_to_send)+","+str(frames_transmitted)+","+str(detection_times)+","
                +str(end_time)+","+str(interval)+"\n")