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
from traffic.utility import IpFilter
from .forms import ControlForm
from .forms import ContactForm
import dateutil.parser
from pytz import timezone
import datetime
import csv
import netaddr
import logging


logger = logging.getLogger('traffic.views')


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
    locationNameList = []
    selectedLocation = ""
    sgNameList = []
    selectedSgName = ""
    detectorList = []
    selectedDetectorList = []
    selectedDetector = ""
    timeIntervalList = ["5", "10", "15", "30", "60", "120"]
    version_number = settings.VERSION

    defaultTimezone = timezone('Europe/Helsinki')
    
 

    # Select performance
    try:
        selectedPerformance = request.POST['performance']
    except(KeyError):
        selectedPerformance = "greenDuration"

    # Simple complementary and explanation of measurements
    infoMeasurementDict = {"Active_green": "In this plot, the distance between two adjacent bar of green phases represents the red and amber duration between them.",
                           "Queue_length": "In this plot, the queue is recorded at the end of red both in number of vehicles and estimated meters.",
                           "Arrival_on_green_ratio": "In this plot, the scattered points represent ratio of volume and number of vehicles during green, and the line is their regression linear",
                           "Arrival_on_green_pecent": "In this plot, it records the percentage of vehicles arriving during green phases in the time interval.",
                           "Comparison_arrival_on_green": "In this plot, it illustrates the measurement 'arrival_on_green' from multile detectors.",
                           "Comparison_arrival_on_green_ratio": "In this plot, it shows 'arrival on green_ratio' from the multiple detectors you selected.",
                           "Volume": "In the plot, it calculates the volume of vehicles arriving the intersection through a detector in the time interval",
                           "Comparison_volume": "In the plot, it shows the volumes from multiple detectors.",
                           "Maximum_capacity": "In the plot, it estimates the maximum number of vehicles being able to pass the intersection from a detector during the green timing of selected interval.",
                           "Green_duration": "In this plot, it calculates the duration of every green phase.",
                           "Green_time_in_interval": "In this plot, it calculates the total timing of green during every selected time interval.",
                           "Percent_of_green_duration": "In this plot, it calculates the percentage of green phases in the cycle.",
                           "Saturation_flow_rate": "In this plot, it estimates saturation flow rate through detectors."
                           }
    try:
        selectedInfoMeasurement = infoMeasurementDict[selectedPerformance]
    except(KeyError):
        selectedInfoMeasurement = None

    # Select location
    locationNameListAll = sorted(get_location_name_list())

    userIp = request.META['REMOTE_ADDR']

    if 'logFilteredLocations' in request.GET:
        locationDefinedList = []
        for key in settings.IP_RANGE_DICT.keys():
            if IpFilter().isIpAllowed(request.META['REMOTE_ADDR'], settings.IP_RANGE_DICT[key][0]):
                for prefix in settings.IP_RANGE_DICT[key][1]:
                    locationDefinedList += [i for i in locationNameListAll if
                                            i.lower().startswith(prefix)]
        locationUndefinedList = [x for x in locationNameListAll if x not in locationDefinedList]

        if locationUndefinedList:
            logger.info('Uncleared location names: %s', locationUndefinedList)

    for key in settings.IP_RANGE_DICT.keys():
        if IpFilter().isIpAllowed(userIp, settings.IP_RANGE_DICT[key][0]):
            locationNameList = []
            for prefix in settings.IP_RANGE_DICT[key][1]:
                locationNameList = locationNameList + [i for i in locationNameListAll if i.lower().startswith(prefix)]

    try:
        selectedLocation = request.POST['location']
    except(KeyError):
        if locationNameList:
            selectedLocation = locationNameList[0]

    # Select signalGroup
    if selectedLocation:
        sgNameDict = get_sg_config_in_one(selectedLocation)
        sgNameList = list(sgNameDict.values())

    try:
        selectedSgName = request.POST['signalGroup']
    except(KeyError):
        if sgNameList:
            selectedSgName = sgNameList[0]

    # Select detector
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
    else:
        detectorListInSelectedLocation = []

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
            logger.warning('Failed to parse start time! Lack of user input validation - check it!')
    if not endTimeString:
        endTime = datetime.datetime.now(defaultTimezone)
    else:
        try:
            endTimeString = endTimeString + datetime.datetime.now(defaultTimezone).strftime(' %z')
            endTime = datetime.datetime.strptime(endTimeString, '%d.%m.%Y %H:%M %z')
        except(ValueError):
            endTime = datetime.datetime.now(defaultTimezone)
            logger.warning('Failed to parse end time! Lack of user input validation - check it!')

    measuresList = sorted(["Saturation_flow_rate", "Percent_of_green_duration", "Green_duration",
                           "Queue_length", "Active_green", "Maximum_capacity",
                           "Arrival_on_green_percent", "Volume", "Arrival_on_green_ratio", "Comparison_volume",
                           "Comparison_arrival_on_green", "Comparison_arrival_on_green_ratio", "Green_time_in_interval"])



    refreshType = request.POST.get('refreshType', "")
    image = ""
    if refreshType == "Plot" and startTimeString and endTimeString:
        if selectedPerformance == "Green_duration" or selectedPerformance == "Percent_of_green_duration":
            image,uuid_name = get_green_time_2(selectedLocation, startTime, endTime, selectedPerformance)
            
            
        elif selectedPerformance == "Saturation_flow_rate":
            image, uuid_name= get_saturation_flow_rate(selectedLocation, selectedSgName, startTime, endTime) 
            
        elif selectedPerformance == "Queue_length":
            image,uuid_name = get_queue_length(selectedLocation, selectedSgName, selectedDetector, startTime, endTime)
            
            
        elif selectedPerformance == "Active_green":
            image, uuid_name = get_green_time(selectedLocation, selectedSgName, startTime, endTime )
            
        elif selectedPerformance == "Maximum_capacity":
            image, uuid_name = get_maxCapacity(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime)
            
        elif selectedPerformance == "Arrival_on_green_percent":
            image, uuid_name = get_arrival_on_green(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, selectedPerformance)
            
        elif selectedPerformance == "Volume":
            image, uuid_name = get_volume_lanes(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime)
            
        elif selectedPerformance == "Arrival_on_green_ratio":
            image, uuid_name = get_arrival_on_green(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, selectedPerformance )           
            
        elif selectedPerformance == "Comparison_volume" or selectedPerformance == "Comparison_arrival_on_green" or selectedPerformance == "Comparison_arrival_on_green_ratio":
            image, uuid_name = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList, selectedTimeInterval, startTime, endTime, selectedPerformance)
            
        elif selectedPerformance == "Green_time_in_interval":
            image, uuid_name = get_green_time_in_interval(selectedLocation, selectedTimeInterval, startTime, endTime )
    else:
        uuid_name = 0
            
    csv_filename = str(uuid_name) + '.csv'
    csv_file_path =temp_folder_path + str(uuid_name) +'.csv'   
    
    csv_file ="traffic/"+csv_filename  
    request.session['uniqueId'] = csv_filename   
    request.session['selectedPerformance'] = selectedPerformance
    
    context = {'locationNameList': locationNameList,
               'selectedPerformance': selectedPerformance,
               'selectedInfoMeasurement': selectedInfoMeasurement,
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
               'form': form,
               'image': image,
               'version_number' : version_number,
               'csv_filename': csv_filename}


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
    csv_filename = request.session['uniqueId']
    performance = request.session['selectedPerformance'] 
    current_time_str =datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return download_file(temp_folder_path+csv_filename, performance + current_time_str+'.csv') 
    


def download_user_manual(request):
    
    with open("traffic/static/traffic/UserManual.pdf", 'rb') as pdf:
        file_path = "traffic/static/traffic/UserManual.pdf"
        content_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(pdf.read(), content_type=content_type)
        response['Content-Disposition'] = 'inline;filename=ImAnalyst_user_manual.pdf'
        return response
    pdf.closed    

