# __________________
# Imtech CONFIDENTIAL
# __________________
#
#  [2015] Imtech Traffic & Infra Oy
#  All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of Imtech Traffic & Infra Oy and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Imtech Traffic & Infra Oy
# and its suppliers and may be covered by Finland and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Imtech Traffic & Infra Oy.
# __________________

import matplotlib.dates as mdates
from matplotlib import pylab
from pylab import *
from pytz import timezone
from dateutil import parser
import uuid
import numpy as np

from .process import *

matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')

GREEN = "GREEN"
AMBER = "AMBER"
RED = "RED"
UNKNOWN = "UNKNOWN"

green_state_group = ["1", "3", "4", "5", "6", "7", "8", ":"]

# The drivable_state_list includes green_state_list, fix amber, vehicle actuated amber and red/amber state.
drivable_state_group = ["1", "3", "4", "5", "6", "7", "8", ":", "0", "<", ">"]

colors = ['skyblue', 'blue', 'c', 'purple', 'red', '#890303', 'black', '#ECE51C', '#FF33FF', '#CC9966',
          '#669900', '#915C0B', '#006600', '#DBFF86', '#99FFFF', '#006666', '#c0c0c0', '#666666']


def get_green_time(location_name, sg_name, time1, time2, green_state_list):
    """get_green_time is the function to visualize active green and passive green for a single selected signal group.
       The parameters are the name of location, the name of the signal group , the start time, end time and green_state_list.
       The plot has two sub plots based on two different definition of active and passive green.
    """
    passive_green_state_list = ["4"] 
    sg_status = get_sg_status(location_name, sg_name, time1, time2) 
    green_on = False
    passive_green_on = False
    active_green_list = []
    start_green_time_list = []
    useless_green_list = []
    total_passive_green_state_time_list = []
    active_green_time_state_list = []
    start_green_time = None
    width = 0.0005
    total_passive_green_state_time = 0
    active_green_state_time = 0
    uuid_name = uuid.uuid4()

    f = open_csv_file(uuid_name, ["start_green_time", "active_green_duration(seconds)",
                                  "passive_green_duration(seconds)",
                                  "active_green_duration_from_grint", "passive_green_from_grint"])
    if sg_status:
        for s in sg_status:
    
            # Start to be green
            if not green_on and s[1] in green_state_list:
                start_green_time = s[0]
                green_on = True
                any_detectors_occupied = True
                detector_unoccupied_lastest_time = s[0]
            # During green
            elif green_on and s[1] in green_state_list:
    
                if int(s[3]) != 0:  # some detectors are occupied
                    any_detectors_occupied = True
                elif int(s[3]) == 0 and any_detectors_occupied:  # record the start that detectors become occupied to unoccupied.
                    detector_unoccupied_lastest_time = s[0]
                    any_detectors_occupied = False
    
                # for the state passive_green part
                elif s[1] in passive_green_state_list and not passive_green_on:
                    passive_green_on = True
                    passive_green_start_time = s[0]
                elif s[1] not in passive_green_state_list and passive_green_on:
                    passive_green_on = False
                    current_passive_green_state_time = timedelta.total_seconds(s[0] - passive_green_start_time)
                    total_passive_green_state_time = total_passive_green_state_time + current_passive_green_state_time
    
            elif green_on and s[1] not in green_state_list:
                green_on = False
                passive_green_on = False
                active_green = timedelta.total_seconds(detector_unoccupied_lastest_time - start_green_time)
                total_green = timedelta.total_seconds(s[0] - start_green_time)
                start_green_time_list.append(start_green_time)
                active_green_list.append(active_green)
                active_green_state_time = total_green - total_passive_green_state_time
                active_green_time_state_list.append(active_green_state_time)
                total_passive_green_state_time_list.append(total_passive_green_state_time)
    
                useless_green = timedelta.total_seconds(s[0] - detector_unoccupied_lastest_time)
                useless_green_list.append(useless_green)
                write_row_csv(f, [start_green_time, active_green, useless_green,
                                  active_green_state_time, total_passive_green_state_time])
                total_passive_green_state_time = 0
        close_csv_file(f)
    
        fig = plt.figure(figsize=(10, 6), facecolor='#99CCFF')
        fig.suptitle('Signalgroup Green Duration: sg ' + sg_name + ' in ' + location_name, fontsize=14, fontweight='bold')
    
        ax = fig.add_subplot(211)  # fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
        helsinkiTimezone = timezone('Europe/Helsinki')
        fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
        fmt2 = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
        set_xaxis_datetime_limit(ax, fmt2, time1, time2)
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6)
    
        green_active = ax.bar(start_green_time_list, active_green_list, width, color='g', edgecolor="none")
        green_useless = ax.bar(start_green_time_list, useless_green_list, width, color='blue', bottom=active_green_list, edgecolor="none")
    
        ax2 = fig.add_subplot(212)
        set_xaxis_datetime_limit(ax2, fmt, time1, time2)
        plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6)
        green_active_state = ax2.bar(start_green_time_list, active_green_time_state_list, width, color='r', edgecolor="none")
        green_passive_state = ax2.bar(start_green_time_list, total_passive_green_state_time_list, width, color='y',
                                      bottom=active_green_time_state_list, edgecolor="none")
        if green_active and green_useless:
            ax.legend((green_active[0], green_useless[0]), ("active green", "passive green"))
        if green_active_state and green_passive_state:
            ax2.legend((green_active_state[0], green_passive_state[0]), ("grint active green", "grint passive green"))
        plt.xlabel('Time')
        ylabel('Green duration(s)')
        return getBufferImage(fig), uuid_name  
    else:
        raise ValueError('No data is valid!')



def get_queue_length(location_name, sg_name, det_name,time_interval, time1, time2, green_state_list):      
    """Function get_queue_length is used to calculate that until the end of red,
       the number of vehicles in the queue and the length of queue in meters.
       The parameters of the function include location name, signal name, detector name, the start time and end time.
       The plot is a bar chart with dual y-axis.
    """    
    sg_det_status = get_sg_det_status(location_name,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
    
    green_on = True
    
    discharge_queue_time = None
    
    detector_occupied = False
    
    count_vehicle_in_queue = 0 
    
    count_vehicle_in_queue_dict = {}
    
    average_length_per_vehicle = 6 

    uuid_name = uuid.uuid4()
    f = open_csv_file(uuid_name, ["discharge_queue_time", "number of vehicles", "The length of queue(meters)"])

    for s in sg_det_status:
        
        if not green_on and s[2] not in green_state_list: #Not green
            if not detector_occupied and s[3] == '1': #vehicle comes
                detector_occupied = True
                count_vehicle_in_queue = count_vehicle_in_queue +1 
            elif detector_occupied and s[3] == '0':   #vehicle leaves 
                detector_occupied = False
        elif not green_on and s[2] in green_state_list: #start green
            green_on = True
        
            
        elif green_on and s[2] not in green_state_list:  #end green
            green_on =False 
            discharge_queue_time = s[0]
            count_vehicle_in_queue_dict[discharge_queue_time] = count_vehicle_in_queue
            queue_length = count_vehicle_in_queue * average_length_per_vehicle  
            write_row_csv(f, [discharge_queue_time,count_vehicle_in_queue,queue_length])
            count_vehicle_in_queue = 0 
    close_csv_file(f)
    
    fig=get_one_plot_figure()
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    fmt=format_axis_date()
    ax.xaxis.set_major_formatter(fmt) 
    ax.xaxis_date()
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    
    #The segment codes is for marking dual units(dual axis) using matplotlib
    ax.bar(list(count_vehicle_in_queue_dict.keys()), list(count_vehicle_in_queue_dict.values()), width = 0.0005, color='purple', edgecolor = "none")
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
    
    ax2.set_ylabel('Queue length (unit:meter)') 
    
    ay2.yaxis.tick_right()
    ax2.set_ylim(ymin2,ymax2) 
    
    # The second parameter of title is for not overlapping title with yaxis on the top. Title has x and y arguments.
    title('Queue length: sg '+ sg_name+ ' in '+location_name + ' detected by ' + det_name, y =1.05)  
    
    return getBufferImage(fig), uuid_name   


    
  
def get_queue_length_in_interval(location_name, sg_name, det_name,time_interval, time1, time2, green_state_list):      
    """Function get_queue_length is used to calculate that until the end of red,
       the number of vehicles in the queue and the length of queue in meters.
       The parameters of the function include location name, signal name, detector name, the start time and end time.
       The plot is a bar chart with dual y-axis.
    """    
    sg_det_status = get_sg_det_status(location_name,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
    
    green_on = True
    
    discharge_queue_time = None
    
    detector_occupied = False
    
    count_vehicle_in_queue = 0 
    
    count_vehicle_in_queue_dict = {}
    
    average_length_per_vehicle = 6 
    average_vehicle_in_queue_list= []
    average_queue_length_list = []
    max_queue_list = []
    start_time_list = []
    count_vehicle_in_queue_list = []
    uuid_name = uuid.uuid4()
    
    f = open_csv_file(uuid_name, ["start_interval_time", "average number of vehicles","maximum vehicles in queue" "average length of queue(meters)"])
    
    interval = convert_time_interval_str_to_timedelta(time_interval)
    
    if sg_det_status: 
        start_time = sg_det_status[0][0]
        
        for s in sg_det_status:
            
            if not green_on and s[2] not in green_state_list: #Not green
                if not detector_occupied and s[3] == '1': #vehicle comes
                    detector_occupied = True
                    count_vehicle_in_queue = count_vehicle_in_queue +1 
                elif detector_occupied and s[3] == '0':   #vehicle leaves 
                    detector_occupied = False
            elif not green_on and s[2] in green_state_list: #start green
                green_on = True
            
            elif green_on and s[2] not in green_state_list:  #end green
                green_on =False 
                discharge_queue_time = s[0] 
                if discharge_queue_time < start_time + interval:
                    count_vehicle_in_queue_dict[discharge_queue_time] = count_vehicle_in_queue
                    if count_vehicle_in_queue != 0:
                        count_vehicle_in_queue_list.append(count_vehicle_in_queue)   

                else:
                    while(discharge_queue_time > start_time + interval):
                        average_vehicle_in_queue = mean_in_list(count_vehicle_in_queue_list)
                        max_queue = 0
                        if(len(count_vehicle_in_queue_list) > 0):
                            max_queue = max(count_vehicle_in_queue_list)
                        average_queue_length = average_vehicle_in_queue * average_length_per_vehicle  
                        write_row_csv(f, [start_time,average_vehicle_in_queue, max_queue, average_queue_length])
                        start_time_list.append(start_time + interval)
                        average_vehicle_in_queue_list.append(average_vehicle_in_queue)
                        average_queue_length_list.append(average_queue_length)
                        max_queue_list.append(max_queue)
                        count_vehicle_in_queue_dict.clear() 
                        average_vehicle_in_queue = 0 
                        max_queue = 0 
                        count_vehicle_in_queue_list = []
                        start_time = start_time + interval   
                count_vehicle_in_queue = 0
    
        close_csv_file(f)
        
        fig=get_one_plot_figure()
        ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
        fmt=format_axis_date()
        set_xaxis_datetime_limit(ax, fmt, time1, time2)
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6, labeltop='off', top='off')    
        #The segment codes is for marking dual units(dual axis) using matplotlib
        ax.bar(start_time_list, average_vehicle_in_queue_list, width = 0.0005, color='purple', edgecolor = "none")
        ax.plot(start_time_list, max_queue_list, marker = '*', color = 'red')
        xlabel('Times')
        ylabel('Number of vehicles in queue')
        
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
        
        ax2.set_ylabel('Queue length (unit:meter)') 
        
        ay2.yaxis.tick_right()
        ax2.set_ylim(ymin2,ymax2) 
        
        # The second parameter of title is for not overlapping title with yaxis on the top. Title has x and y arguments.
        title('Queue length: sg '+ sg_name+ ' in '+location_name + ' detected by ' + det_name +" in "+ time_interval + " mins", y =1.05)  
        
        return getBufferImage(fig), uuid_name                      

def get_queue(location_name, sg_name, det_name,time_interval, time1, time2, green_state_list): 
    if time_interval =='None':
        return get_queue_length(location_name, sg_name, det_name, time_interval, 
                        time1, time2, 
                        green_state_list)
    else:
        return get_queue_length_in_interval(location_name, sg_name, det_name, 
                                    time_interval, 
                                    time1, 
                                    time2, 
                                    green_state_list)

    
    
        





def get_green_time_2(location_name, sg_name_list, time1, time2, performance, green_state_list): 
    """Function get_green_time_2 is the function that shows the green duration of all the signals in a selected location.
       The parameters include location name, the start time and end time and performance. 
       Especially, performance is the string of the selected performance. 
       Based on the selected performance, the plot shows the green duration of all the signal groups in seconds or in percentage.
    """    
    green_on = False

    start_green_time = None    
    
    main_data = get_main_data(location_name, time1, time2) #main_data[tt,grint,dint,seq] 
    
    sg_dict = get_sg_config_in_one(location_name)

    uuid_name = uuid.uuid4()
    f = open_csv_file(uuid_name, ["sg_name", "start_green_time", "green_duration(seconds)", "cycle_duration", "percent_of_green"])

    fig=get_one_plot_figure()
    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.8, top=0.9, wspace=None, hspace=None)
    ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    fmt=format_axis_date()
    set_xaxis_datetime_limit(ax, fmt, time1, time2)
    plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)    
    
    if sg_name_list:
        for sg_name in sg_name_list:
            sg_index = list(sg_dict.keys())[list(sg_dict.values()).index(sg_name)]
            plot_green_time(sg_name, sg_index, main_data, green_on, start_green_time, uuid_name, f, fig, ax, fmt, 
                               location_name, 
                               time1, time2, 
                               performance, 
                               green_state_list)
    else:
        for sg_index in list(sg_dict.keys()):
            sg_name = sg_dict[sg_index] 
            plot_green_time(sg_name, sg_index, main_data, green_on, 
                           start_green_time, 
                           uuid_name, f, fig, ax, 
                           fmt, location_name, 
                           time1, time2, 
                           performance, 
                           green_state_list)                 
        
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    close_csv_file(f)
    
    return getBufferImage(fig),uuid_name

def plot_green_time(sg_name, sg_index, main_data, green_on, start_green_time, uuid_name, f, fig, ax, fmt, location_name, time1, time2, performance, green_state_list):
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
                percent_green = (minimum_green / cycle_duration) * 100 
                percent_green_list.append(percent_green)
                start_cycle_time_list.append(start_green_time)
            green_on = False 
            minimum_green = timedelta.total_seconds(r[0]-start_green_time) 
            start_green_time_list.append(start_green_time)
            minimum_green_list.append(minimum_green)
            green_end_time = r[0] 
            write_row_csv(f,[sg_name,start_green_time,minimum_green, cycle_duration,percent_green])
            
    if performance == "Green duration":
        ax.plot(start_green_time_list, minimum_green_list, marker='o', linestyle='-', label = "'"+sg_name+"'", color=colors[sg_index]) 
        xlabel('Time')
        ylabel('Green duration in seconds per cycle' )
        title('Signalgroup Green Duration in '+location_name)                
    elif performance == "Percent of green duration":
        ax.plot(start_cycle_time_list, percent_green_list, marker='o', linestyle='-', label = "'"+sg_name+"'",color=colors[sg_index]) 
        xlabel('Time')
        ylabel('The percentate of green duration per cycle(%)' )
        title('The percentage of green Duration in '+location_name)   
    return f, ax 

def get_saturation_flow_rate(location_name, sg_name, time1, time2, green_state_list):
    """Saturation flow rate crossing a signalized stop line is define as the number of vechiles per hour that could cross the line if the signal remained green all of the time 
       The time of passage of the third and last third vehicles over several cycles to determine this value in this function. 
       The first few vehicles and the last vehicles are excluded because of starting up the queue or represent the arrival rate.
    """ 
    main_data = get_main_data(location_name, time1, time2)  # [tt,gint,dint,seq]
    sg_pairs = get_sg_config_in_one(location_name)
    if main_data:
        for idx, name in list(sg_pairs.items()):
            if name == sg_name:
                sg_index = idx
                break      
        det_dict = get_det_config_in_one_sg(location_name, sg_name)
    
        required_vehicle_number = 8
        
        one_hour_in_second = 3600
        
        mean_saturation_by_det_list = []
        xlabel_list = []
    
        uuid_name = uuid.uuid4()
        f = open_csv_file(uuid_name, ["det_name", "saturation_flow_rate"])
        
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
                        time_diff = (detector_occupied_time_list_on_green[successive_vehicle_end_index] - 
                                     detector_occupied_time_list_on_green[successive_vehicle_start_index])/(successive_vehicle_end_index - successive_vehicle_start_index)
                        
                        saturation_flow_rate = one_hour_in_second/time_diff.total_seconds()
                        #saturation_flow_rate_pair =[saturation_flow_rate, detector_occupied_time_list_on_green[0]]
                        #saturation_flow_rate_pair_list.append(saturation_flow_rate_pair)
                        saturation_flow_rate_list.append(saturation_flow_rate)
                    detector_occupied_time_list_on_green = []
                
             
            mean_saturation_by_det = mean_in_list(saturation_flow_rate_list)
            mean_saturation_by_det_list.append(mean_saturation_by_det) 
            xlabel_list.append(det_name)
            write_row_csv(f,[det_name, mean_saturation_by_det])
        close_csv_file(f)
        fig_size = plt.rcParams["figure.figsize"]
        fig_size[0]=10 # resize width
        fig_size[1]=6 # resize height
        plt.bar(list(range(len(mean_saturation_by_det_list))),mean_saturation_by_det_list,width=0.009,color = "r", align='center')
        plt.xticks(list(range(len(mean_saturation_by_det_list))),xlabel_list)
        ylabel("Number of vehicles")
        xlabel("Name of each detector")
        title("Saturation flow rate by detectors in signalGroup "+sg_name +" in "+ location_name) 
        
        return getBufferImage(plt.gcf()), uuid_name     
    else:
        raise ValueError("No data is valid!")



def get_maxCapacity(location_name,sg_name,det_name,time_interval,time1,time2, green_state_list):   
    """The function get_maxCapacity is used to calculate the maximum number of vehicle discharging at some lane during the green time in some interval.
       Its parameters are location name, sg name, detector name, time interval, the start time and the end time.
       The plot is a curve line chart with diamond markers representing values of maximum capacity.
    """    
    if time_interval != "None":
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
        start_time = sg_status[0][0] 

        uuid_name = uuid.uuid4()
        f = open_csv_file(uuid_name, ["start_time", "max_capacity", "green in total(seconds)"])
    
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
                write_row_csv(f,[start_time,max_capacity,sum_green])
                start_time = start_time + time_interval_in_seconds
                sum_green = 0 
                
        addCapacityInList(start_time_list, start_time, sum_green, 
                         max_capacity_list)
        write_row_csv(f,[start_time_list[-1],max_capacity_list[-1],sum_green])
        close_csv_file(f)
        
        fig =get_one_plot_figure()
        ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
        fmt=format_axis_date()
        set_xaxis_datetime_limit(ax, fmt, time1, time2)
        plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
        plt.tick_params(labelsize=6)    
        if max_capacity_list:
            ax.plot(start_time_list,max_capacity_list,marker='D',linestyle='--',color='g')
    
        xlabel('Time')
        ylabel('maximum capacity(unit:number of vehicles)' )
        title('Maximum capacity for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
        
        return getBufferImage(fig), uuid_name   
        

    


def get_arrival_on_green(location_name, sg_name,det_name,time_interval,time1,time2,performance, green_state_list):
    
    """The function get_arrival_on_green is used to count the percentage of vehicles arriving the intersection during green time.
    The parameters include location name, signal name, detector name, time interval, the start time and end time and performance. 
    When the string of performance is "Arrival_on_green_percent", the plot is a bar chart to display the percentage of arrival on green.
    """
    if time_interval != "None": 
        interval = convert_time_interval_str_to_timedelta(time_interval)
        
        sg_det_status = get_sg_det_status(location_name,sg_name, det_name, time1, time2) #[time,seq,sg_stauts, det_status]
        
        green_on = False 
        detector_occupied = False
        number_vehicles_in_green = 0 
        number_vehicles_in_red = 0
        start_time = sg_det_status[0][0] 
        arrival_on_green_percent_format_list = []
        number_vehicle_in_sum_list = []
        start_time_list = []
        number_vehicles_in_green_list = []
    
        uuid_name = uuid.uuid4()
        f = open_csv_file(uuid_name, ["start_time", "vehicles arrived during green", "vehicles in total", "arrival on green(%)"])
    
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
                    write_row_csv(f,[start_time,number_vehicles_in_green, number_vehicle_in_sum,arrival_on_green])
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
            write_row_csv(f,[start_time,number_vehicles_in_green, number_vehicle_in_sum,arrival_on_green])
        close_csv_file(f)
        
        if performance =="Arrival on green percent" or performance == "volume":
            fig =get_one_plot_figure()
            ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
            fmt=format_axis_date()
            set_xaxis_datetime_limit(ax, fmt, time1, time2)
            plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
            plt.tick_params(labelsize=6)        
            if performance =="Arrival on green percent":
                ax.bar(start_time_list,arrival_on_green_percent_format_list,width = 0.001,color='#99CCCC', edgecolor="none")
                xlabel('Time')
                ylabel('percentage of arrival on green (%)' )
                title('Percentage of vehicles arrived during green for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
                return getBufferImage(fig), uuid_name   
                 
            else :
                ax.bar(start_time_list,number_vehicle_in_sum_list,width = 0.003,color='#CC6666', edgecolor="none")
                xlabel('Time')
                ylabel('Volume(number of vehicles)' )
                title('Traffic volume for sg '+ sg_name+ ' via '+ det_name +' in '+location_name)
                return getBufferImage(fig) 
        elif performance =="Arrival on green ratio":
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
            return getBufferImage(fig) , uuid_name        




   
def get_volume_lanes(location_name, sg_name,det_name,time_interval,time1,time2, green_state_list):
    """The function get_volume_lanes is used to calculate the volume by the selected detector.
       The parameters include location name, signal group name, detector name, time interval, the start time and end time.
       The plot displays the volume at the selected detector, and if there is paralleled lanes, the volume counted by the paralleled detector will also be shown in the stack bar.
    """  
    if time_interval != "None":
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
                det_paralleled_dict[det_id] = det_name
    
        uuid_name = uuid.uuid4()
        f = open_csv_file(uuid_name, ["start_time", "name of detector", "volume"])
    
        for det_id in list(det_paralleled_dict.keys()):
            det_name = det_dict[det_id]   
            detector_occupied = False
            start_time = main_data[0][0] 

            volume = 0 
            volume_list=[]
            start_time_list= []
            for s in main_data: 
                if s[0] < start_time + interval:
                    if s[2][det_id] =='1' and not detector_occupied:
                        detector_occupied = True                  
                    elif s[2][det_id] =='0' and detector_occupied:
                        volume =volume + 1
                        detector_occupied = False
                else:
                    volume_list.append(volume) 
                    start_time_list.append(start_time)
                    start_time = start_time + interval
                    write_row_csv(f,[start_time,det_name, volume])
                    volume = 0 
            volume_by_lane_dict[det_name]=volume_list  
     
        close_csv_file(f)
        fig = get_one_plot_figure()
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
                r = ax.bar(start_time_list,det_volume_list,width=0.003,color=colors[i],bottom=bottoms[i],edgecolor="none")
                i=i+1
                bar_renderers.append(r) 
            return bar_renderers
        p.extend(create_subplot(matrix, colors))
            
        xlabel("time")
        ylabel("Amount of vehicles")
        title("Traffic volume for "+ sg_name +" at " + location_name + " in " + time_interval +" mins interval")  
        try:
            legend((x[0] for x in p),labels)
        except:
            pass
        return getBufferImage(fig) ,uuid_name        



def get_compared_arrival_on_green_ratio(location_name,det_name_list,time_interval,time1,time2,performance, green_state_list):
    """This function is used to visualize the arrival on green and volume for multiple detectors.
       The parameters are the string of location name, a list of selected detectors names, string of time interva, the start time, the end time and the string of selected performance.
    """
    if time_interval != 'None':
        main_data = get_main_data(location_name, time1, time2) # tt,grint,dint,seq
        interval = convert_time_interval_str_to_timedelta(time_interval)
    
        uuid_name = uuid.uuid4()
        f = open_csv_file(uuid_name, ["det_name", "start_time", "name of vehicle in green", "volume", "arrival_on_green"])
    
        fig = get_one_plot_figure()
        ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)    
        plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    
        for det_name in det_name_list:
            green_on = False 
            detector_occupied = False
            number_vehicles_in_green = 0 
            number_vehicles_in_red = 0
            start_time = main_data[0][0] 
            arrival_on_green_percent_format_list = []
            number_vehicle_in_sum_list = []
            start_time_list = []
            number_vehicles_in_green_list = []
            row = get_sg_and_det_index_by_det_name(location_name, det_name) 
            sg_index = row[0]
            det_index = row[1]
            det_index_in_selected_list = det_name_list.index(det_name)
            color_index = det_index_in_selected_list % len(colors)
    
            for r in main_data:
                sg_state =r[1][sg_index]
                det_state = r[2][det_index]
                time_in_row = r[0]
    
    
                if r[0] < start_time + interval:
                    if not green_on and sg_state in green_state_list:
                        green_on = True 
                    elif green_on and sg_state in green_state_list:
                        if not detector_occupied and det_state == '1':
                            detector_occupied = True
                            number_vehicles_in_green = number_vehicles_in_green + 1 
                        elif detector_occupied and det_state == '0':
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
    
                    middle_time = start_time + interval/2
                    if number_vehicle_in_sum > 0:
                        number_vehicles_in_green_list.append(number_vehicles_in_green)
                        arrival_on_green = (float(number_vehicles_in_green)/(number_vehicle_in_sum))*100
                        #arrival_on_green_percent_format = "{:.0%}".format(arrival_on_green)
                        arrival_on_green_percent_format_list.append(arrival_on_green)
                        start_time_list.append(middle_time)
    
                        number_vehicle_in_sum_list.append(number_vehicle_in_sum)
                        write_row_csv(f,[det_name, start_time+interval, number_vehicles_in_green,
                                                          number_vehicle_in_sum, arrival_on_green])
    
                    number_vehicles_in_green = 0
                    number_vehicles_in_red = 0
                    start_time = start_time + interval
            if start_time_list and number_vehicles_in_green_list and number_vehicle_in_sum_list and arrival_on_green_percent_format_list:
    
                    if performance == "Comparison volume" or performance =="Comparison arrival on green": 
    
                        #x values are times of a day and using a Formatter to formate them.
                        #For avioding crowding the x axis with labels, using a Locator.
    
                        if performance == "Comparison volume":
                            ax.xaxis.set_major_formatter(format_axis_date()) 
                            set_xaxis_datetime_limit(ax, format_axis_date(), time1, time2)
                            plt.setp( plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
                            plt.tick_params(labelsize=6)  
    
                            if len(start_time_list)==len(number_vehicle_in_sum_list):
                                ax.plot(start_time_list,number_vehicle_in_sum_list,marker ='o',linestyle=':', 
                                        label= det_name,color = colors[color_index])
    
                                ylabel('Volume per ' + time_interval + " minutes")
                                xlabel('Time')
                                title("Volumes in multiple directions at intersection " +
                                      location_name + " per " + time_interval + " minutes")
    
                        else:
                            helsinkiTimezone = timezone('Europe/Helsinki')
                            fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
                            set_xaxis_datetime_limit(ax, fmt, time1, time2)
                            plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
                            plt.tick_params(labelsize=6)
                            ax.plot(start_time_list, arrival_on_green_percent_format_list, marker='o', linestyle='-',
                                    label=det_name, color=colors[color_index])
    
                            ylabel('Percentage of arrival on green')
                            xlabel('Times')
                            title('Arrival on green percentage in multiple directions at ' +
                                  location_name + " per " + time_interval + " minutes")
    
                    elif performance == "Comparison arrival on green ratio":
                        if len(number_vehicles_in_green_list) == len(number_vehicle_in_sum_list) and len(number_vehicles_in_green_list) != 0:
    
                            ax.plot(number_vehicle_in_sum_list, number_vehicles_in_green_list, marker='o', linestyle='.',
                                    label=det_name, color=colors[color_index])
                            ylabel('number of vehicles arriving on green')
                            xlabel('volume')
                            title('Arrival on green ratio in different locations per ' +
                                  time_interval + ' minutes at ' + location_name)
    
        ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
        close_csv_file(f)
    
        return getBufferImage(fig), uuid_name   

        




def get_green_time_in_interval(location_name, sg_name_list, time_interval, time1, time2, performance, green_state_list):
    """The function get_green_time_in_interval counts the sum of green time in a time peroid for all the signal groups in a selected location.
       The parameters include location name, time interval and the start time and the end time.
    """
    
    green_on = False

    start_green_time = None

    interval = convert_time_interval_str_to_timedelta(time_interval)

    main_data = get_main_data(location_name, time1, time2)  # main_data[tt,grint,dint,seq] 

    sg_dict = get_sg_config_in_one(location_name)

    uuid_name = uuid.uuid4()
    f = open_csv_file(uuid_name, ["sg_name", "end_interval_time", "green_duration(seconds)_in_interval", "percent"])

    fig = get_one_plot_figure()

    ax = fig.add_subplot(111)  # fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number) 

    plt.subplots_adjust(left=0.07, bottom=0.1, right=0.8, top=0.9, wspace=None, hspace=None)

    fmt = format_axis_date()
    
    if sg_name_list:
        for sg_name in sg_name_list:
            sg_index = list(sg_dict.keys())[list(sg_dict.values()).index(sg_name)]
            plot_green_time_in_interval(green_on, start_green_time, ax, fmt,f, interval, main_data, sg_index, sg_name, location_name, time_interval, time1, time2, performance, green_state_list)
    else:
        for sg_index in list(sg_dict.keys()):
            sg_name = sg_dict[sg_index]
            plot_green_time_in_interval(green_on, start_green_time, ax, fmt, f, interval,  main_data, sg_index,  sg_name, location_name,  time_interval, time1,  time2, performance,  green_state_list)
            
    ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    
    f.close()

    return getBufferImage(fig), uuid_name



def plot_green_time_in_interval(green_on,start_green_time, ax, fmt, f, interval, main_data,sg_index, sg_name, location_name, time_interval, time1, time2, performance, green_state_list):

    start_time = main_data[0][0]
    minimum_green_list = []
    green_on = False
    start_interval_time_list = []
    green_time_in_interval_list = []
    green_time_percent_in_interval_list = []    
    
    for r in main_data:
        if r[0] < start_time + interval:
            if not green_on and r[1][sg_index] in green_state_list:
                start_green_time = r[0]
                green_on = True

            elif green_on and r[1][sg_index] not in green_state_list:
                minimum_green = timedelta.total_seconds(r[0] - start_green_time)
                green_on = False
                minimum_green_list.append(minimum_green)

        else:
            green_time_in_interval = sum(minimum_green_list)
            start_interval_time_list.append(start_time + interval)
            green_time_in_interval_list.append(green_time_in_interval)
            start_time = start_time + interval
            green_time_percent = green_time_in_interval / (int(time_interval) * 60)
            green_time_percent_in_interval_list.append(green_time_percent)
            write_row_csv(f, [sg_name, start_time, green_time_in_interval, green_time_percent])
            minimum_green_list = []

    set_xaxis_datetime_limit(ax, fmt, time1, time2)
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    plt.tick_params(labelsize=6)
    if performance == "Green duration":
        ax.plot(start_interval_time_list, green_time_in_interval_list, marker='o', linestyle='--', label="'" + sg_name +"'", color=colors[sg_index])
        xlabel('Time')
        ylabel('Green duration in seconds' )
        title("Green time of signals  at " + location_name + " by " + str(time_interval) + " minutes")        
    elif performance == "Percentage of green duration":
        ax.plot(start_interval_time_list, green_time_percent_in_interval_list, marker='o', linestyle='-', label = "'"+sg_name+"'",color=colors[sg_index]) 
        xlabel('Time')
        ylabel('The percentate of green duration')
        title('The percentage of green Duration in '+location_name+ " by " + str(time_interval) + " minutes")
    return ax, f     

def get_green_duration(location_name, sg_name_list, time_interval, time1, time2, performance,green_state_list):
    if time_interval =='None': 
        return get_green_time_2(location_name, sg_name_list, time1, time2, performance, 
                               green_state_list)
    else:
        return get_green_time_in_interval(location_name, sg_name_list, time_interval, time1, 
                                         time2, 
                                         performance, 
                                         green_state_list)

