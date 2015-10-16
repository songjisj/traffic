from .process import *
import matplotlib.dates as mdates
from matplotlib import pylab
from pylab import *
import csv
from pytz import timezone
from dateutil import parser
import shutil
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

GREEN = "GREEN"
AMBER = "AMBER"
RED = "RED"
UNKNOWN = "UNKNOWN"
green_state_list = ["0", "1", "3", "4", "5", "6", "7", "8", ":"]
conn_string = "host='localhost' dbname='tfg-db' user='postgres' password='4097' port='5432'"

#active green
def get_green_time(location_name,sg_name,time1,time2):
   
    activate_green_state_list = ["0","1","3","5","6","7","8",":"] 
    passive_green_state_list = ["4"]
    
    sg_status= get_sg_status(location_name, sg_name, time1, time2) #[time,grint,seq,dint] 
    
    green_on = False
    passive_green_on = False 
    active_green_list = []
    start_green_time_list =[]
    useless_green_list = []
    passive_green_time_state_list= []
    total_passive_green_state_time_list = []
    active_green_time_state_list = []
    start_green_time = None
    width = 0.0005
    green_end_time = None 
    total_passive_green_state_time = 0
    active_green_state_time =0
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["start_green_time","active_green_duration(seconds)","passive_green_duration(seconds)","active_green_duration_from_grint","passive_green_from_grint"], delimiter = ';')
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
            
            #for the state passive_green part
            elif s[1] in passive_green_state_list and not passive_green_on:
                passive_green_on = True 
                passive_green_start_time = s[0] 
            elif s[1] not in passive_green_state_list and passive_green_on:
                passive_green_on = False 
                current_passive_green_state_time = timedelta.total_seconds(s[0]-passive_green_start_time)
                total_passive_green_state_time = total_passive_green_state_time + current_passive_green_state_time
            
        elif green_on and s[1] not in green_state_list:
            green_on = False
            passive_green_on = False 
            active_green = timedelta.total_seconds(detector_unoccupied_lastest_time-start_green_time)
            total_green = timedelta.total_seconds(s[0]-start_green_time)
            start_green_time_list.append(start_green_time) 
            active_green_list.append(active_green)
            active_green_state_time = total_green - total_passive_green_state_time 
            active_green_time_state_list.append(active_green_state_time)
            total_passive_green_state_time_list.append(total_passive_green_state_time)
            
            useless_green = timedelta.total_seconds(s[0]-detector_unoccupied_lastest_time) 
            useless_green_list.append(useless_green)
            f.write("{} {} {} {} {}\n".format(start_green_time,active_green,useless_green,active_green_state_time,total_passive_green_state_time)) 
            total_passive_green_state_time = 0
            
    f.close() #close the file after saving.
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    fig =plt.figure(figsize=(10,6),facecolor='#FFFFCC')  #figsize argument is for resizing the figure.
    fig.suptitle('Signalgroup Green Duration: sg '+ sg_name+ ' in '+location_name, fontsize=14, fontweight='bold')
    

    ax =fig.add_subplot(211) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
    fmt2 = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt2)    
    ax.xaxis_date()
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)
    green_active = ax.bar(start_green_time_list, active_green_list,width,color='g')
    green_useless = ax.bar(start_green_time_list,useless_green_list,width,color='#CCFFFF',bottom = active_green_list)    
   
    ax2 = fig.add_subplot(212) 
    ax2.xaxis.set_major_formatter(fmt)
    ax2.xaxis_date()
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')    
    plt.tick_params(labelsize=6)
    green_active_state = ax2.bar(start_green_time_list,active_green_time_state_list, width, color ='r')
    
    green_passive_state = ax2.bar(start_green_time_list,total_passive_green_state_time_list, width, color='y', bottom = active_green_time_state_list)
    if green_active and green_useless:
        ax.legend((green_active[0], green_useless[0]),("active green", "passive green"))
    if green_active_state and green_passive_state:
        ax2.legend((green_active_state[0], green_passive_state[0]),("grint active green","grint passive green"))
    plt.xlabel('Time')
    ylabel('Green duration(s)')    
    return getBufferImage(fig)    


def get_capacity(location_name,sg_name,det_name,time1,time2):   
    
    sg_det_status = get_sg_det_status(location_name,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
     
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

    
    #write csv file
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    f.writelines(["headway", str(headway),'\n'])
    f.writelines(["saturation_flow_rate", str(mean_saturation),'\n'])
    f.writelines(["maximum_capacity", str(round(maximum_capacity)),'\n'])
    f.close 
    
    #plot 
    
    y = [mean_saturation,maximum_capacity]
    x = list(range(len(y)))
    plt.bar(x,y,width=0.1,color = "blue")
    
    return getBufferImage(plt.gcf())

def get_queue_length(location_name,sg_name,det_name,time1,time2): 
    
        
    
    sg_det_status = get_sg_det_status(location_name,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
    
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
        
            count_vehicle_in_queue = 0 
        elif green_on and s[2] not in green_state_list:
            green_on =False 
            discharge_queue_time = s[0]
            count_vehicle_in_queue_dict[discharge_queue_time] = count_vehicle_in_queue
            queue_length = count_vehicle_in_queue * average_length_per_vehicle
            f.write("{} {} {}\n".format(discharge_queue_time,count_vehicle_in_queue,queue_length))                 
    f.close() 
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    fig =plt.figure(figsize=(10,6),facecolor='#669999')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    
    
    #The following segment codes is for formatting xaxis and show the correct time in Helsinki timezone.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt) 
    ax.xaxis_date()
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    
    #The segment codes is for marking dual units(dual axis) using matplotlib
    ax.bar(list(count_vehicle_in_queue_dict.keys()),list(count_vehicle_in_queue_dict.values()),width = 0.0005, color='purple')
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
    
    
    
    return getBufferImage(fig)

def get_green_time_2(location_name, time1,time2,performance): 
    
    green_on = False

    start_green_time = None    
    
    
    main_data = get_main_data(location_name, time1, time2) #main_data[tt,grint,dint,seq] 
    
    sg_dict = get_sg_config_in_one(location_name)
    
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["sg_name","start_green_time","green_duration(seconds)","cycle_duration","percent_of_green"], delimiter = ';')
    writer.writeheader()   
    
    fig =plt.figure(figsize=(10,6),facecolor='#8FBC8F')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    
    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone) 
    ax.xaxis.set_major_formatter(fmt)   
    ax.xaxis_date()
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    

    
    for sg_index in list(sg_dict.keys()):
        sg_name = sg_dict[sg_index] 
        minimum_green_list = []
        start_green_time_list =[]
        cycle_duration_list =[]
        start_cycle_time_list = []
        percent_green_list = []
        green_on = False
        cycle_duration = 0
        percent_green = 0 
        count = 0 
        for r in main_data:
            if not green_on and r[1][sg_index] in green_state_list:
                start_green_time = r[0]
                green_on = True
                
                
            elif green_on and r[1][sg_index] not in green_state_list:
                count = count +1 
                if count>1:
                    cycle_duration = timedelta.total_seconds(r[0] - green_end_time )
                    cycle_duration_list.append(cycle_duration)
                    minimum_green = timedelta.total_seconds(r[0]-start_green_time)
                    percent_green = minimum_green / cycle_duration
                    percent_green_list.append(percent_green)
                    start_cycle_time_list.append(start_green_time)
                green_on = False 
                minimum_green = timedelta.total_seconds(r[0]-start_green_time) 
                start_green_time_list.append(start_green_time)
                minimum_green_list.append(minimum_green)
                green_end_time = r[0] 
                f.write("{} {} {} {} {}\n".format(sg_name,start_green_time,minimum_green,cycle_duration,percent_green)) 

            
        if performance == "Green_duration":
            ax.plot(start_green_time_list, minimum_green_list, marker='o', linestyle='-', label = "sg"+sg_name) 
            xlabel('Time')
            ylabel('Green duration(seconds) per cycle' )
            title('Signalgroup Green Duration in '+location_name)                
        if performance == "Percent_of_green_duration":
            ax.plot(start_cycle_time_list, percent_green_list, marker='o', linestyle='-', label = "sg"+sg_name) 
            xlabel('Time')
            ylabel('The percent of green duration per cycle' )
            title('The percentage of green Duration in '+location_name)                
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    f.close() 
    
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    return getBufferImage(fig)


#Saturation flow rate crossing a signalized stop line is define as the number of vechiles per hour that could cross the line if the signal remained green all of the time 
#The time of passage of the third and last third vehicles over several cycles to determine this value in this function. 
#The first few vehicles and the last vehicles are excluded because of starting up the queue or represent the arrival rate.  
def get_saturation_flow_rate(location_name,sg_name,time1,time2):
    
    main_data = get_main_data(location_name,  time1, time2)  #[tt,gint,dint,seq]
    sg_pairs = get_sg_config_in_one(location_name)
    for idx, name in list(sg_pairs.items()):
        if name == sg_name:
            sg_index = idx
            break      
    det_dict = get_det_config_in_one_sg(location_name, sg_name)


    required_vehicle_number = 8
    
    one_hour_in_second = 3600
    
    mean_saturation_by_det_list = []
    xlabel_list = []
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["det_name","saturation_flow_rate"], delimiter = ';')
    writer.writeheader()    
    
    for det_index in list(det_dict.keys()):
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
    
    
    plt.bar(list(range(len(mean_saturation_by_det_list))),mean_saturation_by_det_list,width=0.009,color = "r", align='center')
    plt.xticks(list(range(len(mean_saturation_by_det_list))),xlabel_list)
    ylabel("Number of vehicles")
    xlabel("Name of each detector")
    title("Saturation flow rate by detectors in signalGroup "+sg_name +" in "+ location_name) 
    
    return getBufferImage(plt.gcf())


def get_maxCapacity(location_name,sg_name,det_name,time_interval,time1,time2):
    

    
    time_interval_in_seconds = convert_time_interval_str_to_timedelta(time_interval)
    
    
    sg_status= get_sg_status(location_name, sg_name, time1, time2) #[time,grint,seq,dint] 
    green_on = False
    sum_green_list = []
    start_time_list = []
    max_capacity_list =[]
    start_green_time = None
    width = 0.0005 
    green_end_time = None 
    sum_green = 0 
    try:
        start_time = sg_status[0][0] 
    except:
        start_time = "10/07/2015 19:00:00" 
    
    
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
    
    
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt)
    ax.xaxis_date() 
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    
   
    ax.plot(start_time_list,max_capacity_list,marker='D',linestyle='--',color='g')

    
    xlabel('Time')
    ylabel('maximum capacity(unit:number of vehicles)' )
    title('Maximum capacity for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
    
    return getBufferImage(fig)    
    
    


def get_arrival_on_green(location_name, sg_name,det_name,time_interval,time1,time2,performance):

    interval = convert_time_interval_str_to_timedelta(time_interval)
    
    sg_det_status = get_sg_det_status(location_name,sg_name, det_name, time1, time2) #[time,seq,sg_stauts, det_status]
    
    green_on = False 
    detector_occupied = False
    number_vehicles_in_green = 0 
    number_vehicles_in_red = 0
    try:
        start_time = sg_det_status[0][0] 
    except:
        start_time = "10/07/2015 19:00" 
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
    
    if performance =="Arrival_on_green_percent" or performance == "volume":
        fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
        ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
        
        #x values are times of a day and using a Formatter to formate them.
        #For avioding crowding the x axis with labels, using a Locator.
        helsinkiTimezone = timezone('Europe/Helsinki')
        fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
        ax.xaxis.set_major_formatter(fmt) 
        ax.xaxis_date() 
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6)        
        if performance =="Arrival_on_green_percent":
            ax.bar(start_time_list,arrival_on_green_percent_format_list,width = 0.001,color='#99CCCC')
            xlabel('Time')
            ylabel('percentage of arrival on green (%)' )
            title('Percentage of vehicles arrived during green for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
            return getBufferImage(fig)   
             
        else :
            ax.bar(start_time_list,number_vehicle_in_sum_list,width = 0.003,color='#CC6666')
            xlabel('Time')
            ylabel('Volume(number of vehicles)' )
            title('Traffic volume for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
            return getBufferImage(fig) 
    elif performance =="Arrival_on_green_ratio":
        fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
        
        plt.scatter(number_vehicle_in_sum_list,number_vehicles_in_green_list)
        
        #Linear regression
        try:
            fit = np.polyfit(number_vehicle_in_sum_list,number_vehicles_in_green_list,1)
            fit_fn = np.poly1d(fit)
            plt.plot(number_vehicle_in_sum_list,number_vehicles_in_green_list,'yo',number_vehicle_in_sum_list,fit_fn(number_vehicle_in_sum_list),'--k')       
        except: 
            pass 
        ylabel('Vehicles arriving on green')
        xlabel('All the vehicles arriving in time interval ' +time_interval+' minutes')
        title("Ratio of vehicles arrived intersection " + location_name + " during green in signalGroup " + sg_name +" via detector " + det_name )
        return getBufferImage(fig)  
        
def get_volume_lanes(location_name, sg_name,det_name,time_interval,time1,time2):
    
    green_on = False 
    
    number_vehicle_in_sum_list = []
    
    number_vehicles_in_green_list = []
    det_paralleled_dict = {}
    volume_by_lane_dict ={}
      
    
    interval = convert_time_interval_str_to_timedelta(time_interval)
   
    main_data = get_main_data(location_name, time1, time2)  #[tt,gint,dint,seq]
    
    
    lane_by_det = det_name.split('_')[0] #Split det_name by '_', obtain the first part.
    
    det_dict = get_det_config_in_one_sg(location_name, sg_name) 
    sg_pairs = get_sg_config_in_one(location_name)
    for idx, name in list(sg_pairs.items()):
        if name == sg_name:
            sg_index = idx
            break   
    #Look for any detector paralleled with the selected one.
    for det_id, det_name in list(det_dict.items()):
        if det_name.startswith(lane_by_det):
            det_paralleled_dict[det_id]=det_name 
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    writer = csv.DictWriter(f, fieldnames = ["start_time","name of detector","volume"], delimiter = ';')
    writer.writeheader()     
    
    for det_id in list(det_paralleled_dict.keys()):
        det_name = det_dict[det_id]
        
        detector_occupied = False
        try:
            start_time = main_data[0][0] 
        except:
            start_time = "10/07/2015 19:00"
        volume = 0 
        volume_list=[]
        start_time_list= []
        for s in main_data: 
            if s[0] < start_time + interval:
                if s[2][det_id] =='1' and not detector_occupied:
                    detector_occupied = True                  
                elif s[2][det_id] =='0' and detector_occupied:
                    volume =volume +1
                    detector_occupied = False
            else:
                volume_list.append(volume) 
                start_time_list.append(start_time)
                start_time = start_time + interval
                f.write("{} {} {}\n".format(start_time,det_name, volume)) 
                volume = 0 
        volume_by_lane_dict[det_name]=volume_list  
    f.close()
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")     
    
    fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
     
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt)     
    ax.xaxis_date() 
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    
    matrix = np.array(list(volume_by_lane_dict.values()))
    p = []
    colors = ['skyblue', 'blue', 'c', 'purple']
    labels = list(volume_by_lane_dict.keys())    
    def create_subplot(matrix,colors):
        bottoms = np.cumsum(np.vstack((np.zeros(matrix.shape[1]), matrix)), axis=0)[:-1]
        i= 0
        bar_renderers = [] 
    
        for det_name, det_volume_list in list(volume_by_lane_dict.items()):
            r = ax.bar(start_time_list,det_volume_list,width=0.003,color=colors[i],bottom=bottoms[i])
            i=i+1
            bar_renderers.append(r) 
        return bar_renderers
    p.extend(create_subplot(matrix, colors))
        
    xlabel("time")
    ylabel("Amount of vehicles")
    title("Traffic volume for "+ sg_name +" at " + location_name)  
    try:
        legend((x[0] for x in p),labels)
    except:
        pass
    return getBufferImage(fig)

def get_compared_arrival_on_green_ratio(location_name,det_name_list,time_interval,time1,time2,performance):
   
    
    main_data = get_main_data(location_name, time1, time2) # tt,grint,dint,seq
    interval = convert_time_interval_str_to_timedelta(time_interval)
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    writer = csv.DictWriter(f, fieldnames = ["det_name","start_time","name of vehicle in green","volume","arrival_on_green"], delimiter = ';')
    writer.writeheader()   
    
    fig =plt.figure(figsize=(10,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)    
    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    
    for det_name in det_name_list:
        green_on = False 
        detector_occupied = False
        number_vehicles_in_green = 0 
        number_vehicles_in_red = 0
        try:
            start_time = main_data[0][0] 
        except:
            start_time = "10/07/2015 19:00"
            
        arrival_on_green_percent_format_list = []
        number_vehicle_in_sum_list = []
        start_time_list = []
        number_vehicles_in_green_list = []         
        row = get_sg_and_det_index_by_det_name(location_name, det_name) 
        sg_index = row[0]
        det_index = row[1] 
        for r in main_data: 
            sg_state =r[1][sg_index]
            det_state = r[2][det_index]
            time_in_row = r[0]

            
            if r[0] < start_time + interval:
                if not green_on and sg_state in green_state_list:
                    green_on = True 
                elif green_on and sg_state in green_state_list:
                    if not detector_occupied and det_state =='1':
                        detector_occupied = True
                        number_vehicles_in_green = number_vehicles_in_green + 1 
                    elif detector_occupied and det_state =='0': 
                        detector_occupied = False
                        
                elif green_on and sg_state not in green_state_list:
                    green_on = False 
                elif not green_on and sg_state not in green_state_list:
                    if not detector_occupied and det_state == '1':
                        detector_occupied = True
                        number_vehicles_in_red = number_vehicles_in_red + 1 
                    elif detector_occupied and det_state == '0':
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
                    f.write("{} {} {} {} {}\n".format(det_name,start_time,number_vehicles_in_green, number_vehicle_in_sum,arrival_on_green))
                number_vehicles_in_green = 0
                number_vehicles_in_red = 0 
                start_time= start_time + interval    
                
        if performance =="Comparison_volume" or performance =="Comparison_arrival_on_green": 

        
            #x values are times of a day and using a Formatter to formate them.
            #For avioding crowding the x axis with labels, using a Locator.
            
            if performance =="Comparison_volume":
                helsinkiTimezone = timezone('Europe/Helsinki')
                fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
                ax.xaxis.set_major_formatter(fmt) 
                ax.xaxis_date() 
                plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
                plt.tick_params(labelsize=6)                 
                ax.plot(start_time_list,number_vehicle_in_sum_list,marker ='o',linestyle=':', label= det_name)
                ylabel('Volume per' + time_interval +"minutes")
                xlabel('Time')
                title("Comparison of volumes in multiple directions at intersection " + location_name + " per " + time_interval +" minutes")            
            else:   
                helsinkiTimezone = timezone('Europe/Helsinki')
                fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
                ax.xaxis.set_major_formatter(fmt) 
                ax.xaxis_date() 
                plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
                plt.tick_params(labelsize=6)                 
                ax.plot(start_time_list,arrival_on_green_percent_format_list, marker ='*',linestyle='-',label=det_name)
                ylabel('Percentage of arrival on green')
                xlabel('Times') 
                title('Comparison of arrival on green percentage in multiple directions at ' + location_name + " per " + time_interval +" minutes")
        elif performance =="Comparison_arrival_on_green_ratio":
                        
            ax.plot(number_vehicle_in_sum_list,number_vehicles_in_green_list,marker ='o', linestyle ='.', label = det_name)
            #Linear regression
            #try:
                #fit = np.polyfit(number_vehicle_in_sum_list,number_vehicles_in_green_list,1)
                #fit_fn = np.poly1d(fit)
                #plt.plot(number_vehicle_in_sum_list,number_vehicles_in_green_list,'yo',number_vehicle_in_sum_list,fit_fn(number_vehicle_in_sum_list),'--k')  
            #except:
                #pass 
            ylabel('number of vehicles arriving on green')
            xlabel('volume')
            title('Comparison of arrival on green ratio in different locations per ' + time_interval +' minutes at ' + location_name )
      
      
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)

    return getBufferImage(fig)          
        
def get_green_time_in_interval(location_name, time_interval,time1,time2): 
    
    green_on = False

    start_green_time = None    
    
    interval = convert_time_interval_str_to_timedelta(time_interval)
    
    main_data = get_main_data(location_name, time1, time2) #main_data[tt,grint,dint,seq] 
    
    sg_dict = get_sg_config_in_one(location_name)
    
    print(sg_dict) 
    
    try:
        start_time = main_data[0][0] 
    except:
        start_time = "10/07/2015 19:00"    
        
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
        
    writer = csv.DictWriter(f, fieldnames = ["sg_name","start_interval_time","green_duration(seconds)_in_interval"], delimiter = ';')
    writer.writeheader()       
    
    fig =plt.figure(figsize=(10,6),facecolor='#8FBC8F')  #figsize argument is for resizing the figure.
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    
    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone) 
 

    for sg_index in list(sg_dict.keys()):
        
        sg_name = sg_dict[sg_index] 
        minimum_green_list = []
        start_green_time_list =[]
        green_on = False
        start_interval_time_list =[]
        green_time_in_interval_list = []
        
        for r in main_data:
            if r[0] < start_time + interval:
                if not green_on and r[1][sg_index] in green_state_list:
                    start_green_time = r[0]
                    green_on = True
                    
                elif green_on and r[1][sg_index] not in green_state_list:
                    minimum_green = timedelta.total_seconds(r[0]-start_green_time)
                    green_on = False 
                    minimum_green_list.append(minimum_green)
                    
            else: 
                green_time_in_interval = sum(minimum_green_list)  
                start_interval_time_list.append(start_time) 
                green_time_in_interval_list.append(green_time_in_interval) 
                
                f.write("{} {} {}  \n".format(sg_name,start_time,green_time_in_interval)) 
                minimum_green_list = []
                start_time = start_time + interval 
        ax.xaxis.set_major_formatter(fmt)   
        ax.xaxis_date()
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6)                   
        ax.plot(start_interval_time_list,green_time_in_interval_list,marker = 'o', linestyle = '--',label = sg_name)
        print(sg_name)
        
            
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    f.close() 
    
    shutil.copyfile("traffic/static/traffic/result.csv", "traffic/static/traffic/result.txt")
    
    return getBufferImage(fig)