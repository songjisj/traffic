from process import get_config_string,getBufferImage,connect_db,disconnect_db,rowNumber,get_location_id,get_sg_config_in_one,get_det_config_in_one_sg,get_det_in_one_location,get_sg_det_status,get_sg_status,get_main_data,mean_in_list,convert_time_interval_str_to_timedelta,addCapacityInList,create_plot_define_format
import psycopg2.extras 
import datetime
from operator import itemgetter
from datetime import timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import pylab
from pylab import *
import PIL
import PIL.Image
import StringIO
from django.conf import settings
import csv
from pytz import timezone
from dateutil import parser
import shutil
import numpy as np 
from scipy.optimize import curve_fit
from scipy.integrate import odeint

GREEN = "GREEN"
AMBER = "AMBER"
RED = "RED"
UNKNOWN = "UNKNOWN"
green_state_list = ["0","1","3","4","5","6","7","8",":"] 


#active green
def get_green_time(location_name, conn_string,sg_name,time1,time2):
    #read configuration file
    conn_string = get_config_string('config.cfg','Section1','conn_string') 
    sg_status= get_sg_status(location_name, conn_string, sg_name, time1, time2) #[time,grint,seq,dint] 
    green_on = False
    active_green_list = []
    start_green_time_list =[]
    useless_green_list = []
    #state "0" represents "red/amber", that occurs before green state but drivers are allowed to go. Here we regards it as green, but actually it is not.
    
    start_green_time = None
    width = 0.0005
    
    green_end_time = None 
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["start_green_time","active_green_duration(seconds)","useless_green_duration(seconds)"], delimiter = ';')
    writer.writeheader()    
    
    for s in sg_status:
        
        # start to be green
        if not green_on and s[1] in green_state_list: 
            start_green_time = s[0] 
            green_on = True
            any_detectors_occupied = True 
            detector_unoccupied_lastest_time = s[0]
        #During green 
        elif green_on and s[1] in green_state_list:
            
            if int(s[3]) != 0 : #som detectors are occupied 
                any_detectors_occupied = True 
            elif  int(s[3]) == 0 and any_detectors_occupied:  # record the start that detectors become occupied to unoccupied.
                detector_unoccupied_lastest_time = s[0]
                any_detectors_occupied = False 
                
            
        elif green_on and s[1] not in green_state_list:
            green_on = False
            active_green = timedelta.total_seconds(detector_unoccupied_lastest_time-start_green_time)
            start_green_time_list.append(start_green_time) 
            active_green_list.append(active_green)
            useless_green = timedelta.total_seconds(s[0]-detector_unoccupied_lastest_time) 
            useless_green_list.append(useless_green)
            f.write("{} {} {}\n".format(start_green_time,active_green,useless_green)) 
            print active_green,start_green_time
            
    f.close() #close the file after saving.
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    fig =plt.figure(figsize=(10,6),facecolor='#FFFFCC')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax.xaxis_date() 
    
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt)    
   
    green_active = ax.bar(start_green_time_list, active_green_list,width,color='g')
    green_useless = ax.bar(start_green_time_list,useless_green_list,width,color='#CCFFFF',bottom = active_green_list)
    if green_active and green_useless:
        ax.legend((green_active[0], green_useless[0]),("active green", "passive green"))
    
    xlabel('Time')
    ylabel('Green duration(s)' )
    title('Signalgroup Green Duration: sg '+ sg_name+ ' in '+location_name)
    
    return getBufferImage()    



#Function get_saturation_flow_rate return a list of saturation flow rate and timestamp 
#Saturation flow rate crossing a signalized stop line is define as the number of vechiles per hour that could cross the line if the signal remained green all of the time 
#The time of passage of the third and last third vehicles over several cycles to determine this value in this function. 
#The first few vehicles and the last vehicles are excluded because of starting up the queue or represent the arrival rate.  
def get_capacity(location_name,conn_string,sg_name,det_name,time1,time2):
    conn_string = get_config_string('config.cfg','Section1','conn_string')    
    
    sg_det_status = get_sg_det_status(location_name,conn_string,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
     
    green_on = False
     
    detector_occupied = False 
     
    detector_occupied_time = None
     
    count_vehicle = 0 
     
    detector_occupied_time_list_on_green = []
     
    successive_vehicle_end_index = 6
     
    successive_vehicle_start_index =2
     
    time_diff = 0
    
    time_diff_list = []
     
    start_green_time = None
     
    start_green_time_list = [] 
     
    saturation_flow_rate = 0 
     
    saturation_flow_rate_list = []
    
    saturation_flow_rate_pair_list = []
    
    sum_green_duration = 0 
     
    for s in sg_det_status:
        if not green_on and s[2] in green_state_list:
            green_on =True
            start_green_time = s[0]
            start_green_time_list.append(start_green_time)
        elif green_on and s[2] in green_state_list:
            if not detector_occupied and s[3]=="1":
                detector_occupied_time = s[0]
                detector_occupied = True
                detector_occupied_time_list_on_green.append(detector_occupied_time) 
                count_vehicle = count_vehicle+1
                 
            elif detector_occupied and s[3]=="0":
                detector_occupied = False 
        elif green_on and s[2] not in green_state_list:
            green_on =False 
            sum_green_duration = timedelta.total_seconds(s[0]-start_green_time) + sum_green_duration 

            if len(detector_occupied_time_list_on_green) > 10: 
                time_diff=(detector_occupied_time_list_on_green[successive_vehicle_end_index]-detector_occupied_time_list_on_green[successive_vehicle_start_index])/4
                saturation_flow_rate = 3600/time_diff.total_seconds()  
                time_diff_list.append(time_diff.total_seconds())
                saturation_flow_rate_pair = [saturation_flow_rate,detector_occupied_time_list_on_green[1]]
                saturation_flow_rate_pair_list.append(saturation_flow_rate_pair) 
                saturation_flow_rate_list.append(saturation_flow_rate)
            detector_occupied_time_list_on_green = []
            count_vehicle = 0 
    mean_saturation = mean_in_list(saturation_flow_rate_list)
    headway = mean_in_list(time_diff_list)
    maximum_capacity = mean_saturation * sum_green_duration / (parser.parse(time2) - parser.parse(time1)).total_seconds()
    print saturation_flow_rate_list
    print mean_saturation
    print headway 
    print round(maximum_capacity)  
    
    #write csv file
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    f.writelines(["headway", str(headway),'\n'])
    f.writelines(["saturation_flow_rate", str(mean_saturation),'\n'])
    f.writelines(["maximum_capacity", str(round(maximum_capacity)),'\n'])
    f.close 
    
    #plot 
    
    y = [mean_saturation,maximum_capacity]
    x = range(len(y))
    plt.bar(x,y,width=0.1,color = "blue")
    
    return getBufferImage()

def get_queue_length(location_name,conn_string,sg_name,det_name,time1,time2): 
    
    conn_string = get_config_string('config.cfg','Section1','conn_string')     
    
    sg_det_status = get_sg_det_status(location_name,conn_string,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
    
    green_on = True
    
    
    discharge_queue_time = None
    
    detector_occupied = False
    
    count_vehicle_in_queue = 0 
    
    count_vehicle_in_queue_dict = {}
    
    average_length_per_vehicle = 8 
    
    # "w+" means empty the file before starting writing.
    f = open("traffic/static/traffic/result.csv","w+")
    
    #Write header
    writer = csv.DictWriter(f, fieldnames = ["discharge_queue_time","number of vehicles","The length of queue(meters)"], delimiter = ';')
    writer.writeheader()        
    
    for s in sg_det_status:
        
        if not green_on and s[2] not in green_state_list:
            if not detector_occupied and s[3] == '1':
                detector_occupied = True
                count_vehicle_in_queue = count_vehicle_in_queue +1 
            elif detector_occupied and s[3] == '0':
                detector_occupied = False
        elif not green_on and s[2] in green_state_list:
            green_on = True
            discharge_queue_time = s[0]
            count_vehicle_in_queue_dict[discharge_queue_time] = count_vehicle_in_queue
            queue_length = count_vehicle_in_queue * average_length_per_vehicle
            f.write("{} {} {}\n".format(discharge_queue_time,count_vehicle_in_queue,queue_length))             
            count_vehicle_in_queue = 0 
        elif green_on and s[2] not in green_state_list:
            green_on =False 
    f.close() 
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    fig =plt.figure(figsize=(10,6),facecolor='#669999')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax.xaxis_date()
    
    #The following segment codes is for formatting xaxis and show the correct time in Helsinki timezone.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt) 
    
    #The segment codes is for marking dual units(dual axis) using matplotlib
    ax.bar(count_vehicle_in_queue_dict.keys(),count_vehicle_in_queue_dict.values(),width = 0.0005, color='purple')
    xlabel('Times')
    ylabel('Number of vehicles in queue' )
    
    #Define limits of figures
    ymin = 0
    ymax = 15 
    
    #first plot
    ax.set_ylim(ymin,ymax)
    ax.yaxis.tick_left()
    
    #Second plot
    ax2 =twinx()
    
    ax2.axes.get_xaxis().set_visible(False) # Tring to hide the x-axes of second plot but I don't know it did not work
    ax2.get_xaxis().tick_bottom() 
    
    ay2 = twiny()  
    
    #Function 'yconv' convert the number of vehicles in queue to length of queue in metre 
    def yconv(y):
        return y * average_length_per_vehicle
    
    ymin2 = yconv(ymin)
    ymax2 = yconv(ymax)
    
    ax2.set_ylabel('queue length (unit:meter)') 
    
    ay2.yaxis.tick_right()
    ax2.set_ylim(ymin2,ymax2) 
    
    # The second parameter of title is for not overlapping title with yaxis on the top. Title has x and y arguments.
    title('Queue length: sg '+ sg_name+ ' in '+location_name + 'detected by' + det_name, y =1.05)  
    
    
    
    return getBufferImage()

def get_green_time_2(location_name, conn_string,time1,time2):
    
    green_on = False

    start_green_time = None    
    conn_string = get_config_string('config.cfg','Section1','conn_string') 
    
    main_data = get_main_data(location_name, conn_string, time1, time2) #main_data[tt,grint,dint,seq] 
    
    sg_dict = get_sg_config_in_one(location_name, conn_string)
    
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["sg_name","start_green_time","green_duration(seconds)"], delimiter = ';')
    writer.writeheader()   
    
    fig =plt.figure(figsize=(10,6),facecolor='#8FBC8F')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax.xaxis_date()
    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)  
    ax.xaxis.set_major_formatter(fmt)    
    xlabel('Time')
    ylabel('Green duration(s)' )
    title('Signalgroup Green Duration in '+location_name)    
    
    for sg_index in sg_dict.keys():
        sg_name = sg_dict[sg_index] 
        minimum_green_list = []
        start_green_time_list =[]
        green_on = False
        for r in main_data:
            if not green_on and r[1][sg_index] in green_state_list:
                start_green_time = r[0]
                green_on = True
            elif green_on and r[1][sg_index] not in green_state_list:
                green_on = False 
                minimum_green = timedelta.total_seconds(r[0]-start_green_time) 
                start_green_time_list.append(start_green_time)
                minimum_green_list.append(minimum_green)
                
                f.write("{} {} {}\n".format(sg_name,start_green_time,minimum_green)) 
        
        ax.plot(start_green_time_list, minimum_green_list, marker='o', linestyle='-', label = "sg"+sg_name) 
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    f.close() 
    
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    return getBufferImage()


#Saturation flow rate crossing a signalized stop line is define as the number of vechiles per hour that could cross the line if the signal remained green all of the time 
#The time of passage of the third and last third vehicles over several cycles to determine this value in this function. 
#The first few vehicles and the last vehicles are excluded because of starting up the queue or represent the arrival rate.  
def get_saturation_flow_rate(location_name,conn_string,sg_name,time1,time2):
    conn_string = get_config_string('config.cfg','Section1','conn_string') 
    main_data = get_main_data(location_name, conn_string, time1, time2)  #[tt,gint,dint,seq]
    sg_pairs = get_sg_config_in_one(location_name, conn_string)
    for idx, name in sg_pairs.items():
        if name == sg_name:
            sg_index = idx
            break      
    det_dict = get_det_config_in_one_sg(location_name, sg_name, conn_string)


    required_vehicle_number = 8
    
    one_hour_in_second = 3600
    
    mean_saturation_by_det_list = []
    xlabel_list = []
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["det_name","saturation_flow_rate"], delimiter = ';')
    writer.writeheader()    
    
    for det_index in det_dict.keys():
        det_name = det_dict[det_index]

        green_on = False
        
        detector_occupied = False 
    
        detector_occupied_time = None
    
        detector_occupied_time_list_on_green = []
    
        successive_vehicle_end_index = 7
    
        successive_vehicle_start_index =3
    
        time_diff = 0
    
        time_diff_list = []
    
        start_green_time = None
    
        start_green_time_list = [] 
    
        saturation_flow_rate = 0 
    
        saturation_flow_rate_list = []
    
        saturation_flow_rate_pair_list = []
    
        sum_green_duration = 0  
        
        for r in main_data:
            if not green_on and r[1][sg_index] in green_state_list:
                green_on = True
                start_green_time = r[0]
                start_green_time_list.append(start_green_time)
            elif green_on and r[1][sg_index] in green_state_list:
                if not detector_occupied and r[2][det_index] == '1':
                    detector_occupied_time = r[0]
                    detector_occupied = True
                    detector_occupied_time_list_on_green.append(detector_occupied_time)
                elif detector_occupied and r[2][det_index] =='0':
                    detector_occupied = False 
            elif green_on and r[1][sg_index] not in green_state_list:
                green_on = False
                #sum_green_duration = timedelta.total_seconds(r[0]-start_green_time) + sum_green_duration
                if len(detector_occupied_time_list_on_green) > required_vehicle_number:
                    time_diff = (detector_occupied_time_list_on_green[successive_vehicle_end_index] - detector_occupied_time_list_on_green[successive_vehicle_start_index])/(successive_vehicle_end_index - successive_vehicle_start_index)
                    saturation_flow_rate = one_hour_in_second/time_diff.total_seconds()
                    #saturation_flow_rate_pair =[saturation_flow_rate, detector_occupied_time_list_on_green[0]]
                    #saturation_flow_rate_pair_list.append(saturation_flow_rate_pair)
                    saturation_flow_rate_list.append(saturation_flow_rate)
                detector_occupied_time_list_on_green = []
            
         
        mean_saturation_by_det = mean_in_list(saturation_flow_rate_list)
        mean_saturation_by_det_list.append(mean_saturation_by_det) 
        xlabel_list.append(det_name)
        f.write("{} {}\n".format(det_name, mean_saturation_by_det)) 
    f.close()
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")  
    
    
    plt.bar(range(len(mean_saturation_by_det_list)),mean_saturation_by_det_list,width=0.009,color = "r", align='center')
    plt.xticks(range(len(mean_saturation_by_det_list)),xlabel_list)
    ylabel("Number of vehicles")
    xlabel("name of each detector")
    title("Saturation flow rate by detectors in signalGroup "+sg_name +" in "+ location_name) 
    
    return getBufferImage()


def get_maxCapacity(location_name,sg_name,det_name,conn_string,time_interval,time1,time2):
    
    from pytimeparse.timeparse import timeparse
    import datetime 
    
    time_interval_in_seconds = datetime.timedelta(seconds=timeparse(time_interval))
    conn_string = get_config_string('config.cfg','Section1','conn_string') 
    
    sg_status= get_sg_status(location_name, conn_string, sg_name, time1, time2) #[time,grint,seq,dint] 
    green_on = False
    sum_green_list = []
    start_time_list = []
    max_capacity_list =[]
    start_green_time = None
    width = 0.0005 
    green_end_time = None 
    sum_green = 0 
    start_time = sg_status[0][0] # start time of each time interval 
    
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["start_time","max_capacity","green in total(seconds)"], delimiter = ';')
    writer.writeheader()   
    
    # the sum of green time in a time interval 
    for s in sg_status:
        if not green_on and s[1] in green_state_list:
            start_green_time = s[0]
            green_on = True
        elif green_on and s[1] not in green_state_list:
            green_on = False 
            green_duration = (s[0]-start_green_time).total_seconds()
            sum_green = sum_green + green_duration
        elif s[0] >= start_time + time_interval_in_seconds:
            max_capacity = addCapacityInList(start_time_list, start_time, sum_green, 
                             max_capacity_list)
            f.write("{} {} {}\n".format(start_time,max_capacity,sum_green))
            start_time = start_time + time_interval_in_seconds
            sum_green = 0 
            
    addCapacityInList(start_time_list, start_time, sum_green, 
                     max_capacity_list)
    f.write("{} {} {}\n".format(start_time_list[-1],max_capacity_list[-1],sum_green))
    f.close()
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")  
    
    fig =plt.figure(figsize=(10,6),facecolor='#FFFF99')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax.xaxis_date() 
    
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt)
   
    ax.plot(start_time_list,max_capacity_list,marker='D',linestyle='--',color='g')

    
    xlabel('Time')
    ylabel('maximum capacity(unit:number of vehicles)' )
    title('Maximum capacity for sg '+ sg_name+ 'via '+ det_name +' in '+location_name)
    
    getBufferImage()    
    
    


def get_arrival_on_green(location_name,conn_string, sg_name,det_name,time_interval,time1,time2,performance):

    interval = convert_time_interval_str_to_timedelta(time_interval)
    conn_string = get_config_string('config.cfg','Section1','conn_string') 
    sg_det_status = get_sg_det_status(location_name, conn_string, sg_name, det_name, time1, time2) #[time,seq,sg_stauts, det_status]
    
    green_on = False 
    detector_occupied = False
    number_vehicles_in_green = 0 
    number_vehicles_in_red = 0
    start_time = sg_det_status[0][0] 
    arrival_on_green_percent_format_list = []
    number_vehicle_in_sum_list = []
    start_time_list = []
    number_vehicles_in_green_list = []

    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    writer = csv.DictWriter(f, fieldnames = ["start_time","vehicles arrived during green","vehicles in total","arrival on green(%)"], delimiter = ';')
    writer.writeheader()     
    
    for s in sg_det_status:
        if s[0] < start_time + interval:
            if not green_on and s[2] in green_state_list:
                green_on = True 
            elif green_on and s[2] in green_state_list:
                if not detector_occupied and s[3] =='1':
                    detector_occupied = True
                    number_vehicles_in_green = number_vehicles_in_green + 1 
                elif detector_occupied and s[3] =='0':
                    detector_occupied = False
                
            elif green_on and s[2] not in green_state_list:
                green_on = False 
            elif not green_on and s[2] not in green_state_list:
                if not detector_occupied and s[3] == '1':
                    detector_occupied = True
                    number_vehicles_in_red = number_vehicles_in_red + 1 
                elif detector_occupied and s[3] == '0':
                    detector_occupied = False
               
        else:
            number_vehicle_in_sum = number_vehicles_in_green + number_vehicles_in_red
            
            if number_vehicle_in_sum > 0:
                number_vehicles_in_green_list.append(number_vehicles_in_green)
                arrival_on_green = (float(number_vehicles_in_green)/(number_vehicle_in_sum))*100
                #arrival_on_green_percent_format = "{:.0%}".format(arrival_on_green)
                arrival_on_green_percent_format_list.append(arrival_on_green)
                start_time_list.append(start_time)
                
                number_vehicle_in_sum_list.append(number_vehicle_in_sum)
                f.write("{} {} {} {}\n".format(start_time,number_vehicles_in_green, number_vehicle_in_sum,arrival_on_green))
            number_vehicles_in_green = 0
            number_vehicles_in_red = 0 
            start_time= start_time + interval   
    
    number_vehicle_in_sum = number_vehicles_in_green + number_vehicles_in_red
    if number_vehicle_in_sum > 0:
        start_time_list.append(start_time)
        arrival_on_green =(float(number_vehicles_in_green)/(number_vehicle_in_sum))*100
        arrival_on_green_percent_format_list.append(arrival_on_green)
        number_vehicles_in_green_list.append(number_vehicles_in_green)
        number_vehicle_in_sum_list.append(number_vehicle_in_sum)
        f.write("{} {} {} {}\n".format(start_time,number_vehicles_in_green, number_vehicle_in_sum,arrival_on_green))

    f.close()   
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")  
    
    if performance =="arrivalOnGreenPercent" or performance == "volume":
        fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
        ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
        ax.xaxis_date() 
        #x values are times of a day and using a Formatter to formate them.
        #For avioding crowding the x axis with labels, using a Locator.
        helsinkiTimezone = timezone('Europe/Helsinki')
        fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
        ax.xaxis.set_major_formatter(fmt) 
        if performance =="arrivalOnGreenPercent":
            ax.bar(start_time_list,arrival_on_green_percent_format_list,width = 0.001,color='#99CCCC')
            xlabel('Time')
            ylabel('percentage of arrival on green (%)' )
            title('percentage of vehicle arrived on green for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
            getBufferImage()   
             
        else :
            ax.bar(start_time_list,number_vehicle_in_sum_list,width = 0.003,color='#CC6666')
            xlabel('Time')
            ylabel('Volumn(number of vehicles)' )
            title('Traffic volumn for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
            getBufferImage()   
    elif performance =="arrivalOnGreenRatio":
        fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
        
        plt.scatter(number_vehicle_in_sum_list,number_vehicles_in_green_list)
        
        
        fit = np.polyfit(number_vehicle_in_sum_list,number_vehicles_in_green_list,1)
        fit_fn = np.poly1d(fit)
        plt.plot(number_vehicle_in_sum_list,number_vehicles_in_green_list,'yo',number_vehicle_in_sum_list,fit_fn(number_vehicle_in_sum_list),'--k')
        
        #def fitfunc(t, k):
            #'Function that returns Ca computed from an ODE for a k'
            #def myode(Ca, t):
                #return -k * Ca
        
            #Green0 = number_vehicles_in_green_list[0]
            #Greensol = odeint(myode, Green0, t)
            #return Greensol[:,0]  
        
        #k_fit, kcov = curve_fit(fitfunc, number_vehicle_in_sum_list, number_vehicles_in_green_list, p0=1.3)
        
        #tfit = np.linspace(0,1);
        #fit = fitfunc(tfit, k_fit) 
        #plt.plot(number_vehicle_in_sum_list, number_vehicles_in_green_list, 'ro', label='data')
        #plt.plot(tfit, fit, 'b-', label='fit')        
        
        ylabel('Vehicles arrived on green')
        title("Ratio of vehicles arrived intersection " + location_name + " on green in signalGroup " + sg_name +" via detector " + det_name )
        getBufferImage()   
        
      
       
            
                
                
            
            