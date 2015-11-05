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

import configparser
import matplotlib.dates as mdates
from matplotlib import pylab
from pylab import *
from io import BytesIO
import psycopg2.extras
from operator import itemgetter
import datetime
from datetime import timedelta
import base64
import csv
from pytz import timezone
from django.db import connection
from django.conf import settings
import uuid 
import tempfile
import mimetypes


temp_folder_path = str(tempfile.mkdtemp())+"\\"


def generate_uuid():
    
    user_filename = uuid.uuid4() 
    return user_filename
    
    
def create_plot_define_format(backgroud_color): 
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10,6),facecolor=backgroud_color)  #figsize argument is for resizing the figure.
    ax = fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)
    ax.xaxis_date()

    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.
    helsinkiTimezone = datetime.timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%H:%M:%S', tz=helsinkiTimezone)
    ax.xaxis.set_major_formatter(fmt)


def get_config_string(config_file,section_number,content):
    config = configparser.RawConfigParser()
    config.read('config.cfg')
    
    conn_string = config.get('Section1','conn_string') 
    return conn_string


def getBufferImage(fig):
    #save image to base64 code string
    imgdata = BytesIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)

    image = base64.encodebytes(imgdata.getvalue())

    #TODO: We should return here a HttpResponse or change the method and utilize http://www.dajaxproject.com/ or other similar

    pylab.close()
    return image
    

#Function to connect to postgresql 
def connect_db():
    #conn = psycopg2.connect(conn_string)
    return connection
    
#Function to disconnect to database       
def disconnect_db(conn): 
    #conn.close() 
    return



""" write a function: the location name of intersection is the only parameter  
    return all the signals and detectors related to it. 
""" 
def get_location_id(location_name,):
    conn = connect_db()
    cursor = conn.cursor() 
    cursor.execute("SELECT cid FROM controller WHERE cname = '" + location_name +"'") 
    location_id = cursor.fetchone()[0]   
    disconnect_db(conn) 
    
    return location_id
    #get_signalgroup = cursor.execute
    
def get_sg_and_det_index_by_det_name(location_name,det_name):
    
    conn = connect_db()
    location_id = get_location_id(location_name)
    cursor = conn.cursor()
    cursor.execute("SELECT sgidx, idx from controller_config_det where fk_cid ='" + str(location_id) +"' AND " +"name = '" +det_name +"'")
    row =cursor.fetchone()
    disconnect_db(conn)
    return row


#Function to get a dictionary that all signals' indexes are keys and names are values when input location_name   
def get_sg_config_in_one(location_name):
    
    
    conn = connect_db()
    location_id = get_location_id(location_name)
    cursor = conn.cursor() 
    cursor.execute("SELECT idx,name from controller_config_sg WHERE fk_cid = '" +str(location_id) +"'") 
    rows = cursor.fetchall()
    signals = {}
    for i in range(len(rows)):
        signals[rows[i][0]] = rows[i][1] 
        
    disconnect_db(conn)
    return signals


#Return a dictionary of all detectors in one intersection, the key is the local index of detector, the value is its name.
# TODO: Seems to be unused, cleanup before first release if not used
def get_det_in_one_location(location_name):
    
    conn = connect_db()
    location_id = get_location_id(location_name)
    cursor = conn.cursor()
    cursor.execute("SELECT idx,name from controller_config_det WHERE fk_cid = '" + str(location_id) + "'")
    rows = cursor.fetchall()
    detectors = {}
    for i in range(len(rows)):
        detectors[rows[i][0]] = rows[i][1]

    disconnect_db(conn)
    return detectors



#Function to get the configuration of detectors in the intersection and the specified signalgroup whose name is provided 
#Return a dictionary detectors, the keys are index of detectors and values are names of detectors.
def get_det_config_in_one_sg(location_name, sg_name):

    conn = connect_db()
    location_id = get_location_id(location_name)
    sg_dict = get_sg_config_in_one(location_name)

    sg_id = -1
    for sg_key in list(sg_dict.keys()):
        if sg_dict[sg_key] == sg_name:
            sg_id = sg_key

    cursor = conn.cursor()
    rows = []
    if sg_id > -1:
        cursor.execute("SELECT idx,name FROM controller_config_det WHERE fk_cid = '" + str(location_id) + "' AND sgidx ='" + str(sg_id) + "'")
        rows = cursor.fetchall()
    detectors = {}
    for i in range(len(rows)):
        detectors[rows[i][0]] = rows[i][1]

    disconnect_db(conn)
    return detectors


def get_main_data(location_name, time1, time2):
    """ Function get_main_data returns raw data whose columns are timestamp, grint, dint.
    :param location_name: Location name = well known intersection name
    :param time1: Time of oldest raw data entry to retrieve, inclusive
    :param time2: Time of latest raw data entry
    :return: Sorted list of raw data
    """
    conn = connect_db()
    location_id = get_location_id(location_name)
    cursor = conn.cursor()
    cursor.execute("SELECT tt, grint, dint,seq FROM tf_raw WHERE fk_cid =  %s AND tt >= %s AND tt < %s", (location_id, time1, time2))
    rows = cursor.fetchall()
    main_data = []
    for i in range(len(rows)):
        rows[i][0].strftime("%Y-%m-%d %H:%M:%S")
        main_data.append(rows[i])
    main_data = sorted(main_data, key=itemgetter(3, 0))

    disconnect_db(conn)
    return main_data

def get_location_name_list():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT distinct cid,  cname FROM controller")
    rows =cursor.fetchall()
    location_name_list =[]
    for i in range(len(rows)):
        location_name_list.append(rows[i][1])
    disconnect_db(conn)
    return location_name_list
    

#This function is used to filter the status of single signalgroup with timestamp.
#Parameters:
#location_name, conn_string, sg_name, start time and end time.
def get_sg_status(location_name,sg_name,time1,time2): 
    
    sg_pairs = get_sg_config_in_one(location_name)
    for idx, name in list(sg_pairs.items()):
        if name == sg_name:
            sg_index = idx
            break   
    main_data = get_main_data(location_name, time1, time2) 
    det_dict_in_the_sg = get_det_config_in_one_sg(location_name, sg_name)
    det_index_list = list(det_dict_in_the_sg.keys())
    sg_status = []
    for i in range(len(main_data)):
        sg_status.append([])
    
    
    for i in range(len(main_data)):
        sg_status[i].append(main_data[i][0])
        sg_status[i].append(main_data[i][1][sg_index])
        sg_status[i].append(main_data[i][3]) #seq number
        det_substring = ""
        for det_index in det_index_list:
            det_substring = det_substring + main_data[i][2][det_index]
        sg_status[i].append(det_substring) # dint for detectors associated with the selected sg_name
        
    sg_status_sorted = sorted(sg_status, key = itemgetter(2,0))
    return sg_status_sorted
    


#This function is used to filter the status of single signalgroup and signal detector with timestamp.
#Parameters:
#location_name, conn_string, sg_name, start time and end time.
def get_sg_det_status(location_name,sg_name,det_name,time1,time2): 
    sg_index = 0
    det_index = 0
    #look for the index of the input sg_name.
    sg_pairs = get_sg_config_in_one(location_name)
    for idx, name in list(sg_pairs.items()):
        if name == sg_name:
            sg_index = idx
            break  
    #look for the index for the input detector.
    det_pairs = get_det_config_in_one_sg(location_name, sg_name)
    for idx, name in list(det_pairs.items()):
        if name==det_name:  
            det_index =idx 
            break 
             
        
    main_data = get_main_data(location_name, time1, time2)
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
 

def convert_time_interval_str_to_timedelta(time_interval):
    
    minutes_to_seconds = int(time_interval)*60
    time_interval_in_seconds = datetime.timedelta(seconds=minutes_to_seconds)  #timeparse('3m') = 180 , convert 3 minutes to 180 second,type is int.
    return time_interval_in_seconds


def addCapacityInList(start_time_list, start_time, sum_green, max_capacity_list):
    default_saturation_flow_rate = 1200 
    start_time_list.append(start_time)
    max_capacity = default_saturation_flow_rate*(sum_green/3600)
    max_capacity_list.append(max_capacity)  
    
    return max_capacity

#def rowNumber():
    
    ##read configuration file
    #config = configparser.RawConfigParser()
    #config.read('config.cfg')
    
    #conn_string = config.get('Section1','conn_string') 
    #conn = psycopg2.connect()
    #cursor = conn.cursor()
    #query = "SELECT fk_cid from controller_config_det"
    #cursor.execute(query)
    #rows = cursor.fetchall()     
    #conn.close()
    #return len(rows) % 2 + 1


def fetch_data(query): 
    conn = connect_db()
    #conn.cursor will return a cursor object, you can use the cursor to perfor queries
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall() 
    disconnect_db(conn)
    return rows 

# fetch configuration data and save in dictionary
# parameter dict_key :select values of a column as the key of dictionary
def config(query,dict_key):
    rows = fetch_data(query)
    dict_data = {}
    for i in range(len(rows)):
        dict_data[rows[i][dict_key]] = rows[i]
    
    return dict_data   

def count_volume_and_arrival_on_green(sg_state,det_state,interval,start_time,time_in_row,green_on,
                                      green_state_list,detector_occupied,number_vehicles_in_red,number_vehicles_in_green,
                                      arrival_on_green_percent_format_list,number_vehicle_in_sum_list,start_time_list,
                                      number_vehicles_in_green_list):
    if time_in_row < start_time + interval:
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
    return(start_time_list,number_vehicle_in_sum_list,arrival_on_green_percent_format_list) 

def open_csv_file(uuid_name,headers_list):
    
    csv_file_path = temp_folder_path + str(uuid_name) +'.csv'
    file = open(csv_file_path,"w+")
    writer = csv.DictWriter(file, fieldnames = headers_list, delimiter = ';')
    writer.writeheader()     
    print(file.name)
    return file

def write_row_csv(file,values):
    writer = csv.writer(file, delimiter=';')
    writer.writerow(values)
    
def get_one_plot_figure():
    fig =plt.figure(figsize=(9,6),facecolor='#99CCFF')  #figsize argument is for resizing the figure.
    #ax =fig.add_subplot(111) #fig.add_subplot equivalent to fig.add_subplot(1,1,1), means subplot(nrows.,ncols, plot_number)    
    #plt.subplots_adjust(left=0.07, bottom=0.1, right=0.85, top=0.9, wspace=None, hspace=None)
    grid(True)
    return fig

def format_axis_date():
    #x values are times of a day and using a Formatter to formate them.
    #For avioding crowding the x axis with labels, using a Locator.    
    helsinkiTimezone = timezone('Europe/Helsinki')
    fmt = mdates.DateFormatter('%m-%d %H:%M:%S', tz=helsinkiTimezone)
    return fmt 

def file_close_and_copy(file):
    import shutil
    file.close()
        
    
    

def set_xaxis_datetime_limit(ax,fmt,xlim1,xlim2):
    ax.xaxis.set_major_formatter(fmt)    
    ax.xaxis_date()
    ax.set_xlim(xlim1,xlim2)     
    
def draw_bar_chart(ax, x_list, y_list, width, color):
    ax.bar(x_list, y_list, width, color='g',edgecolor = "none")

def download_file(file_name, file_download_name):
    import os, tempfile, zipfile
    from django.http import HttpResponse
    from django.core.servers.basehttp import FileWrapper
    from django.conf import settings
    import mimetypes
    file_name = file_name
    download_name = file_download_name
    wrapper = FileWrapper(open(file_name))
    content_type = mimetypes.guess_type(file_name)[0]
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-length'] = os.path.getsize(file_name)
    response['Content-Disposition'] = "attachment;filename=%s" % download_name
    return response

def download_file2(file_path, file_name):
    from django.utils.encoding import smart_str
    from django.http import HttpResponse
    
    from django.conf import settings
    from django.core.servers.basehttp import FileWrapper
    
    wrapper = FileWrapper(open(file_path))
    content_type = mimetypes.guess_type(file_path)[0]
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
    response['X-Sendfile'] = smart_str(file_path)    
    return response 