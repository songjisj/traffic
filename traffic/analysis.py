

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
import ConfigParser
import csv
from pytz import timezone

from dateutil import parser
import shutil

GREEN = "GREEN"
AMBER = "AMBER"
RED = "RED"
UNKNOWN = "UNKNOWN"



def rowNumber():
    
    #read configuration file
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string') 
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor)
    query = "SELECT fk_cid from controller_config_det"
    cursor.execute(query)
    rows = cursor.fetchall()     
    conn.close()
    return len(rows) % 2 + 1


#Function to connect to postgresql 
def connect_db(conn_string):
    conn = psycopg2.connect(conn_string)
    return conn
    
#Function to disconnect to database       
def disconnect_db(conn):
    
    conn.close() 
   
def fetch_data(conn_string,query): 
    conn = connect_db(conn_string)
    #conn.cursor will return a cursor object, you can use the cursor to perfor queries
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor)
    cursor.execute(query)
    rows = cursor.fetchall() 
    disconnect_db(conn)
    return rows 

# fetch configuration data and save in dictionary
# parameter dict_key :select values of a column as the key of dictionary
def config(conn_string,query,dict_key):
    rows = fetch_data(conn_string, query)
    dict_data = {}
    for i in range(len(rows)):
        dict_data[rows[i][dict_key]] = rows[i]
    
    
    return dict_data

# write a function: the location name of intersection is the only parameter  
# return all the signals and detectors related to it. 
def get_location_id(location_name,conn_string):
    conn = connect_db(conn_string)
    cursor = conn.cursor() 
    cursor.execute("SELECT cid FROM controller WHERE cname = '" + location_name +"'") 
    location_id = cursor.fetchone()[0] 
    
    
    disconnect_db(conn) 
    
    return location_id
    #get_signalgroup = cursor.execute

#Function to get a dictionary that all signals' indexes are keys and names are values when input location_name   
def get_sg_config_in_one(location_name,conn_string):
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string')     
    conn = connect_db(conn_string)
    location_id = get_location_id(location_name, conn_string)
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor) 
    cursor.execute("SELECT idx,name from controller_config_sg WHERE fk_cid = '" +str(location_id) +"'") 
    rows = cursor.fetchall()
    signals = {}
    for i in range(len(rows)):
        signals[rows[i][0]] = rows[i][1]
        
    disconnect_db(conn)
    return signals


#Return a dictionary of all detectors in one intersection, the key is the local index of detector, the value is its name.
def get_det_in_one_location(location_name,conn_string):
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
        
    conn_string = config.get('Section1','conn_string')        
    conn = connect_db(conn_string)    
    location_id = get_location_id(location_name, conn_string)
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor) 
    cursor.execute("SELECT idx,name from controller_config_det WHERE fk_cid = '" +str(location_id) +"'") 
    rows = cursor.fetchall()
    detectors = {}
    for i in range(len(rows)):
        detecotrs[rows[i][0]] = rows[i][1]
        
    disconnect_db(conn)
    return detectors 


#Function to get the configuration of detectors in the intersection and the specified signalgroup whose name is provided 
#Return a dictionary detectors, the keys are index of detectors and values are names of detectors.
def get_det_config_in_one_sg(location_name,sg_name,conn_string): 
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
        
    conn_string = config.get('Section1','conn_string')        
    conn = connect_db(conn_string)
    location_id = get_location_id(location_name, conn_string)
    sg_dict = get_sg_config_in_one(location_name, conn_string)
    
    sg_id = -1
    for sg_key in sg_dict.keys():
        if sg_dict[sg_key] == sg_name:
            sg_id = sg_key
            
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor)
    rows = []
    if sg_id > -1 :
        cursor.execute("SELECT idx,name FROM controller_config_det WHERE fk_cid = '" + str(location_id) +"' AND sgidx ='" +str(sg_id)+"'")
        rows = cursor.fetchall()
    detectors = {}
    for i in range(len(rows)):
        detectors[rows[i][0]] = rows[i][1]
        
    disconnect_db(conn)
    return detectors

#Function get_main_data returns raw data whose columns are timestamp, grint, dint
#Parameters: location_name, conn_string, the selected start time and end time.
def get_main_data(location_name,conn_string, time1,time2):
    conn = connect_db(conn_string)
    location_id = get_location_id(location_name, conn_string)
    cursor = conn.cursor('cursor_unique_name', cursor_factory = psycopg2.extras.DictCursor)
    cursor.execute("SELECT tt, grint, dint,seq FROM tf_raw WHERE fk_cid = '" + str(location_id) + "' AND tt >= '" + str(time1) + "' AND tt < '" + str(time2)+"'")
    rows =cursor.fetchall()
    main_data = []
    for i in range(len(rows)):
        rows[i][0].strftime("%Y-%m-%d %H:%M:%S")
        main_data.append(rows[i])
    main_data = sorted(main_data,key=itemgetter(3,0))
    
    disconnect_db(conn)
    return main_data 


#This function is used to filter the status of single signalgroup with timestamp.
#Parameters:
#location_name, conn_string, sg_name, start time and end time.
def get_sg_status(location_name,conn_string,sg_name,time1,time2): 
    sg_pairs = get_sg_config_in_one(location_name, conn_string)
    for idx, name in sg_pairs.items():
        if name == sg_name:
            sg_index = idx
            break   
    main_data = get_main_data(location_name, conn_string, time1, time2)
    sg_status = []
    for i in range(len(main_data)):
        sg_status.append([])
    
    for i in range(len(main_data)):
        sg_status[i].append(main_data[i][0])
        sg_status[i].append(main_data[i][1][sg_index])
        sg_status[i].append(main_data[i][3]) #seq number
        sg_status[i].append(main_data[i][2])
        
    sg_status_sorted = sorted(sg_status, key = itemgetter(2,0))
    return sg_status_sorted
    


#This function is used to filter the status of single signalgroup and signal detector with timestamp.
#Parameters:
#location_name, conn_string, sg_name, start time and end time.
def get_sg_det_status(location_name,conn_string,sg_name,det_name,time1,time2): 
    sg_index = 0
    det_index = 0
    #look for the index of the input sg_name.
    sg_pairs = get_sg_config_in_one(location_name, conn_string)
    for idx, name in sg_pairs.items():
        if name == sg_name:
            sg_index = idx
            break  
    #look for the index for the input detector.
    det_pairs = get_det_config_in_one_sg(location_name, sg_name, conn_string)
    for idx, name in det_pairs.items():
        if name==det_name:  
            det_index =idx 
            break 
             
        
    main_data = get_main_data(location_name, conn_string, time1, time2)
    sg_status = []
    for i in range(len(main_data)):
        sg_status.append([])
        

    for i in range(len(main_data)):
        rowtime = main_data[i][0].strftime('%Y-%m-%d %H:%M:%S')
        sg_status[i].append(main_data[i][0]) #time 
        sg_status[i].append(main_data[i][3]) #seq number
        sg_status[i].append(main_data[i][1][sg_index])  # sg_state 
        sg_status[i].append(main_data[i][2][det_index])
    sg_det_status_sorted = sorted(sg_status, key = itemgetter(1,0))
    return sg_det_status_sorted 

#active green
def get_green_time(location_name, conn_string,sg_name,time1,time2):
    #read configuration file
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    conn_string = config.get('Section1','conn_string')  
    sg_status= get_sg_status(location_name, conn_string, sg_name, time1, time2) #[time,grint,seq,dint] 
    green_on = False
    active_green_list = []
    start_green_time_list =[]
    useless_green_list = []
    #state "0" represents "red/amber", that occurs before green state but drivers are allowed to go. Here we regards it as green, but actually it is not.
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
    start_green_time = None
    width = 0.0005
   
    
    green_end_time = None 
    
    f = open("traffic/static/traffic/result.csv","w+") #create a csv file to save data in.
    
    writer = csv.DictWriter(f, fieldnames = ["start_green_time","active_green_duration(seconds),useless_green_duration(seconds)"], delimiter = ';')
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
            elif  int(s[3]) == 0:
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
    
    fig =plt.figure(figsize=(10,6),facecolor='#FFE6E6')  #figsize argument is for resizing the figure.
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
        ax.legend((green_active[0], green_useless[0]),("active green", "useless green"))
    
    xlabel('Time')
    ylabel('Green duration(s)' )
    title('Signalgroup Green Duration: sg '+ sg_name+ ' in '+location_name)
    
    return getBufferImage()

def getBufferImage():
    buffer = StringIO.StringIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.fromstring("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save("traffic/static/traffic/plot.png", "PNG")
    pylab.close();
    

    
def signalState(sgStateCode):   
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
    amber_state_list=[";","<","=",">","I"]
    red_state_list=["9","?","@","A","B","C","D","E","F","G","H","J"]
    Unknown_state ="."
    if sgStateCode in green_state_list:
        return GREEN
    elif sgStateCode in amber_state_list:
        return AMBER
    elif sgStateCode in red_state_list:
        return RED
    else:
        return UNKNOWN
    
    
def mean_in_list(list):
    mean = 0 
    mean = sum(list)/len(list)
    return mean 


#Function get_saturation_flow_rate return a list of saturation flow rate and timestamp 
#Saturation flow rate crossing a signalized stop line is define as the number of vechiles per hour that could cross the line if the signal remained green all of the time 
#The time of passage of the third and last third vehicles over several cycles to determine this value in this function. 
#The first few vehicles and the last vehicles are excluded because of starting up the queue or represent the arrival rate.  
def get_capacity(location_name,conn_string,sg_name,det_name,time1,time2):
    
    
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string')      
    
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
     
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
     
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
    
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
        
    conn_string = config.get('Section1','conn_string')          
    
    sg_det_status = get_sg_det_status(location_name,conn_string,sg_name,det_name,time1,time2) #sg_det_status[time,seq,grint,dint]
    
    green_on = True
    
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
    
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

    #state "0" represents "red/amber", that occurs before green state but drivers are allowed to go. Here we regards it as green, but actually it is not.
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
    start_green_time = None    
    #read configuration file
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string')  
    
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
def get_capacity_2(location_name,conn_string,sg_name,time1,time2):
    
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    conn_string = config.get('Section1','conn_string')      
    
    main_data = get_main_data(location_name, conn_string, time1, time2)  #[tt,gint,dint,seq]
    sg_pairs = get_sg_config_in_one(location_name, conn_string)
    for idx, name in sg_pairs.items():
        if name == sg_name:
            sg_index = idx
            break      
    det_dict = get_det_config_in_one_sg(location_name, sg_name, conn_string)

    green_state_list = ["0","1","3","4","5","6","7","8",":"]    
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
    fig, ax = plt.subplots()
    ind = np.arange(len(xlabel_list))
    ax.bar(ind,mean_saturation_by_det_list,width=0.001,color = "r")
    ax.set_xticklabels(xlabel_list)
    ax.set_ylabel("Number of vehicles")
    ax.set_title("Saturation flow rate in signalGroup "+sg_name  ) 
    
    
    
    return getBufferImage()


