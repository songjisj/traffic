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

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from traffic.analysis import *
from traffic.process import isIpAllowed
from .forms import ControlForm
from .forms import ContactForm
import dateutil.parser
from pytz import timezone
import datetime
import csv
import netaddr
import logging


# Create your views here.
def home(request):
    return HttpResponse('''
        Login with <a href="login/fb">Facebook</a>.<br />
        Login with <a href="login/tw">Twitter</a>.<br />
        <form action="login/oi">
            <input type="text" name="id" value="me.yahoo.com" />
            <input type="submit" value="Authenticate With OpenID">
        </form>
    ''')

def index(request):
    selectedPerformance = ""
    locationNameListAll=[]
    locationNameList = []
    selectedLocation = ""
    sgNameList = []
    selectedSgName = ""
    detectorList = []
    selectedDetectorList = []
    selectedDetector = ""
    timeIntervalList = ["5", "10", "15", "30", "60", "120"]

    defaultTimezone = timezone('Europe/Helsinki')

    #Select performance 
    try:
        selectedPerformance = request.POST['performance']
    except(KeyError):
        selectedPerformance = "greenDuration"

    #Select location
    locationNameListAll = sorted(get_location_name_list()) 
    
    locationInTampereList = [i for i in locationNameListAll if i.lower().startswith('tre')] 
    
    locationInOuluList = [i for i in locationNameListAll if i.lower().startswith('oulu')] 
    
    locationUndefinedList = [i for i in locationNameListAll if not i.lower().startswith('tre') and not i.lower().startswith('oulu')]
    
    if locationUndefinedList:
        print( locationUndefinedList)
    else:
        print('no uncleared naming of locations')
       
    
    userIp = request.META['REMOTE_ADDR'] 
    print(userIp)
    if isIpAllowed(userIp, settings.TAMPERE_IP_RANGE):
        locationNameList = locationInTampereList
        print(locationInOuluList)
    elif isIpAllowed(userIp, settings.OULU_IP_RANGE):
        locationNameList = locationInOuluList
        print(locationInTampereList)
    

    try:
        selectedLocation = request.POST['location']
    except(KeyError):
        selectedLocation = "TRE303" 

    #Select signalGroup
    if selectedLocation:
        sgNameDict = get_sg_config_in_one(selectedLocation)
        sgNameList = list(sgNameDict.values())

    try:
        selectedSgName = request.POST['signalGroup']
    except(KeyError):
        if sgNameList:
            selectedSgName = sgNameList[0]

    #Select detector
    if selectedSgName and selectedLocation:
        detectorDict = get_det_config_in_one_sg(selectedLocation, selectedSgName)
        detectorList = sorted(list(detectorDict.values()))

    try:
        selectedDetector = request.POST['detector']
    except(KeyError):
        if detectorList:
            selectedDetector = detectorList[0]

    # Select multiple detectors
    if selectedLocation:
        detectorDictInSelectedLocation = get_det_in_one_location(selectedLocation)
        detectorListInSelectedLocation = sorted(list(detectorDictInSelectedLocation.values()))

    try:
        selectedDetectorList = request.POST.getlist('detectors[]')
    except(KeyError):
        if detectorListInSelectedLocation:
            selectedDetectorList = detectorListInSelectedLocation[0:1]

    # Select time interval
    try:
        selectedTimeInterval = request.POST['timeInterval']
    except(KeyError):
        if timeIntervalList:
            selectedTimeInterval = timeIntervalList[0]

    form = ContactForm(request.POST)

    # select start and end time
    startTimeString = request.POST.get('starttime', "")
    endTimeString = request.POST.get('endtime', "")
    if not startTimeString:
        startTime = datetime.datetime.now(defaultTimezone)
    else:
        try:
            startTimeString = startTimeString + datetime.datetime.now(defaultTimezone).strftime(' %z')
            startTime = datetime.datetime.strptime(startTimeString, '%d.%m.%Y %H:%M %z')
        except(ValueError):
            startTime = datetime.datetime.now(defaultTimezone)
            logging.warning('Failed to parse start time! Lack of user input validation - check it!')
    if not endTimeString:
        endTime = datetime.datetime.now(defaultTimezone)
    else:
        try:
            endTimeString = endTimeString + datetime.datetime.now(defaultTimezone).strftime(' %z')
            endTime = datetime.datetime.strptime(endTimeString, '%d.%m.%Y %H:%M %z')
        except(ValueError):
            endTime = datetime.datetime.now(defaultTimezone)
            logging.warning('Failed to parse end time! Lack of user input validation - check it!')

    measuresList = sorted(["Saturation_flow_rate", "Percent_of_green_duration", "Green_duration", "Queue_length", "Active_green",
                           "Maximum_capacity", "Arrival_on_green_percent", "Volume", "Arrival_on_green_ratio", "Comparison_volume",
                           "Comparison_arrival_on_green", "Comparison_arrival_on_green_ratio", "Green_time_in_interval"])

    # display CSV file
    fileReader = csv.reader("traffic/static/traffic/result.csv", delimiter=',')
    lineNum = 0  # initialize line number

    refreshType = request.POST.get('refreshType', "")
    image = ""
    if refreshType == "Plot" and startTimeString and endTimeString:
        if selectedPerformance == "Green_duration":
            image = get_green_time_2(selectedLocation, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Percent_of_green_duration":
            image = get_green_time_2(selectedLocation, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Saturation_flow_rate":
            image = get_saturation_flow_rate(selectedLocation, selectedSgName, startTime, endTime)
        elif selectedPerformance == "Queue_length":
            image = get_queue_length(selectedLocation, selectedSgName, selectedDetector, startTime, endTime)
        elif selectedPerformance == "Active_green":
            image = get_green_time(selectedLocation, selectedSgName, startTime, endTime)
        elif selectedPerformance == "Maximum_capacity":
            image = get_maxCapacity(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime)
        elif selectedPerformance == "Arrival_on_green_percent":
            image = get_arrival_on_green(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Volume":
            image = get_volume_lanes(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime)
        elif selectedPerformance == "Arrival_on_green_ratio":
            image = get_arrival_on_green(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Comparison_volume":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList, selectedTimeInterval, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Comparison_arrival_on_green":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList, selectedTimeInterval, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Comparison_arrival_on_green_ratio":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList, selectedTimeInterval, startTime, endTime, selectedPerformance)
        elif selectedPerformance == "Green_time_in_interval":
            image = get_green_time_in_interval(selectedLocation, selectedTimeInterval,
                                               startTime,
                                               endTime)
    context = {'locationNameList': locationNameList,
               'selectedPerformance': selectedPerformance,
               'measuresList': measuresList,
               'timeIntervalList': timeIntervalList,
               'selectedTimeInterval': selectedTimeInterval,
               'selectedLocation': selectedLocation,
               'sgNameList': sgNameList,
               'selectedSgName': selectedSgName,
               'detectorList': detectorList,
               'detectorListInSelectedLocation': detectorListInSelectedLocation,
               'selectedDetector': selectedDetector,
               'selectedDetectorList': selectedDetectorList,
               'startTimeString': startTime.strftime('%d.%m.%Y %H:%M'),
               'endTimeString': endTime.strftime('%d.%m.%Y %H:%M'),
               'fileReader': fileReader,
               'lineNum': lineNum,
               'form': form,
               'image': image}
    #return HttpResponse(green_example, content_type="image/png")

    return render(request, 'traffic/index.html', context)

def data(request):
    control_form = ControlForm(request.POST)
    if control_form.is_valid():

        return render(request, 'data.html', {'control_form': control_form})

def measuresinfo(request):

    return render(request, 'traffic/measuresinfo.html', "")

def maps(request):
    selectedLocation = request.POST.get('selectedLocatioForMap', "TRE303")
    context = {'selectedLocation': selectedLocation}
    return render(request, 'traffic/maps.html', context)

def download_data_file(request):
    import os, tempfile, zipfile
    from django.core.servers.basehttp import FileWrapper
    from django.conf import settings
    import mimetypes

    filename = "traffic/static/traffic/result.csv"
    download_name = "result.csv"
    wrapper = FileWrapper(open(filename))
    content_type = mimetypes.guess_type(filename)[0]
    response = Httpresponse(wrapper, content_type=content_type)
    response['Content-length'] = os.path.getsize(filename)
    response['Content-Disposition'] = "attachment;filename=%s" % download_name
    return response
