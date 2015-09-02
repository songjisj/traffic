

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
    cursor.execute("SELECT cid FROM controller WHERE cname =" + location_name) 
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
    cursor.execute("SELECT idx,name from controller_config_sg WHERE fk_cid =" +str(location_id)) 
    rows = cursor.fetchall()
    signals = {}
    for i in range(len(rows)):
        signals[rows[i][0]] = rows[i][1]
        
    disconnect_db(conn)
    return signals

#Function to get the configuration of detectors in the intersection and the specified signalgroup whose name is provided 
def get_det_config_in_one(location_name,sg_name,conn_string): 
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
    cursor.execute("SELECT tt, grint, dint FROM tf_raw WHERE fk_cid = " + str(location_id) + "AND tt >=" + str(time1) + " AND tt < " + str(time2))
    rows =cursor.fetchall()
    main_data = []
    for i in range(len(rows)):
        rows[i][0].strftime("%Y-%m-%d %H:%M:%S")
        main_data.append(rows[i])
    
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
        rowtime = main_data[i][0].strftime('%Y-%m-%d %H:%M:%S')
        sg_status[i].append(main_data[i][0])
        sg_status[i].append(main_data[i][1][sg_index])
    sg_status_sorted = sorted(sg_status, key = itemgetter(0))
    return sg_status_sorted

def get_green_time(location_name, conn_string,sg_name,time1,time2):
    #read configuration file
    config = ConfigParser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string')  
    sg_status= get_sg_status(location_name, conn_string, sg_name, time1, time2)
    green_on = False
    minimum_green_list = []
    start_green_time_list =[]
    #state "0" represents "red/amber", that occurs before green state but drivers are allowed to go. Here we regards it as green, but actually it is not.
    green_state_list = ["0","1","3","4","5","6","7","8",":"]
    start_green_time = None
    for s in sg_status:
        if not green_on and s[1] in green_state_list: 
            start_green_time = s[0]
            green_on = True
        elif green_on and s[1] not in green_state_list:
            green_on = False
            minimum_green = timedelta.total_seconds(s[0]-start_green_time)
            start_green_time_list.append(start_green_time) 
            minimum_green_list.append(minimum_green)
            print minimum_green,start_green_time
    
    fig =plt.figure()
    #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax =fig.add_subplot(111)
    ax.xaxis_date()
    average_green_time = sum(minimum_green_list)/len(minimum_green_list)
    
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    fmt = mdates.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(fmt)
   
       
    ax.bar(start_green_time_list, minimum_green_list,width=0.0001,color='g')
    ax.axhline(y=10,xmin=0,xmax=100,linewidth=0.01,color="r",zorder=0)
    

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
    
    




