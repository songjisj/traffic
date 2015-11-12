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
import dateutil.parser
from pytz import timezone
import datetime
import csv
import netaddr
import logging
from django.shortcuts import redirect

logger = logging.getLogger('traffic.views')


# Create your views here.
def home(request):
    return redirect(settings.SESSION_COOKIE_PATH + '/index/')


def index(request):
    selectedPerformance = ""
    locationNameList = []
    selectedLocation = ""
    sgNameList = []
    selectedSgName = ""
    selectedSgNameList = []
    detectorList = []
    selectedDetectorList = []
    green_for_driver = []
    selectedDetector = ""
    timeIntervalList = ["5", "10", "15", "30", "60", "120"]
    version_number = settings.VERSION
    uuid_name = 0 

    defaultTimezone = timezone('Europe/Helsinki')

    checkboxSelection = request.POST.get("drivableTime", "")
    if checkboxSelection == "drivableTimeSelected":
        green_for_driver = drivable_state_group
    else:
        green_for_driver = green_state_group
    print(green_for_driver)

    # Select performance
    try:
        selectedPerformance = request.POST['performance']
    except(KeyError):
        selectedPerformance = "greenDuration"

    # Simple complementary and explanation of measurements
    infoMeasurementDict = {"Active green": "In this plot, the distance between two adjacent bar of green phases represents the red and amber duration between them.",
                           "Queue length": "In this plot, the queue is recorded at the end of red both in number of vehicles and estimated meters.",
                           "Arrival on green ratio": "In this plot, the scattered points represent ratio of volume and number of vehicles during green, and the line is their regression linear",
                           "Arrival_on_green_pecent": "In this plot, it records the percentage of vehicles arriving during green phases in the time interval.",
                           "Comparison arrival on green": "In this plot, it illustrates the measurement 'arrival_on_green' from multile detectors.",
                           "Comparison_Arrival on green ratio": "In this plot, it shows 'arrival on green_ratio' from the multiple detectors you selected.",
                           "Volume": "In the plot, it calculates the volume of vehicles arriving the intersection through a detector in the time interval",
                           "Comparison volume": "In the plot, it shows the volumes from multiple detectors.",
                           "Maximum capacity": "In the plot, it estimates the maximum number of vehicles being able to pass the intersection from a detector during the green timing of selected interval.",
                           "Green duration": "In this plot, it calculates the duration of every green phase.",
                           "Green_time_in_interval": "In this plot, it calculates the total timing of green during every selected time interval.",
                           "Percentage of green duration": "In this plot, it calculates the percentage of green phases in the cycle.",
                           "Saturation flow rate ": "In this plot, it estimates saturation flow rate through detectors."
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
            
    # Select signalGroupList
    try:
        selectedSgNameList = request.POST.getlist('signalGroupList[]')
    except:
        if sgNameList:
            selectedSgNameList = sgNameList[0:1]

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
    if selectedPerformance =="Green duration" or selectedPerformance == "Percentage of green duration":
        timeIntervalList=["5", "10", "15", "30", "60", "120", "None"]
    else:
        timeIntervalList=["5", "10", "15", "30", "60", "120"]
    try:
        selectedTimeInterval = request.POST['timeInterval']
    except(KeyError):
        if timeIntervalList:
            selectedTimeInterval = timeIntervalList[0]

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

    measuresList = sorted(["Saturation flow rate ", "Percentage of green duration", "Green duration",
                           "Queue length", "Active green", "Maximum capacity",
                           "Arrival on green percent", "Volume", "Arrival on green ratio", "Comparison volume",
                           "Comparison arrival on green", "Comparison arrival on green ratio"])



    refreshType = request.POST.get('refreshType', "")
    image = ""
    if refreshType == "Plot" and startTimeString and endTimeString:
        
        if selectedPerformance == "Green duration" or selectedPerformance == "Percentage of green duration":
            timeIntervalList = ["None", "5", "10", "15", "30", "60", "120"]
            image,uuid_name = get_green_duration(selectedLocation, selectedSgNameList , selectedTimeInterval, startTime, endTime, selectedPerformance, green_for_driver)
            
            
        elif selectedPerformance == "Saturation flow rate ":
            image, uuid_name= get_saturation_flow_rate(selectedLocation, selectedSgName, startTime, endTime, green_for_driver) 
            
        elif selectedPerformance == "Queue length":
            image,uuid_name = get_queue_length(selectedLocation, selectedSgName, selectedDetector, startTime, endTime, green_for_driver)
            
            
        elif selectedPerformance == "Active green":
            image, uuid_name = get_green_time(selectedLocation, selectedSgName, startTime, endTime, green_for_driver )
            
        elif selectedPerformance == "Maximum capacity":
            image, uuid_name = get_maxCapacity(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, green_for_driver)
            
        elif selectedPerformance == "Arrival on green percent" or selectedPerformance == "Arrival on green ratio":
            image, uuid_name = get_arrival_on_green(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, selectedPerformance, green_for_driver)
            
        elif selectedPerformance == "Volume":
            image, uuid_name = get_volume_lanes(selectedLocation, selectedSgName, selectedDetector, selectedTimeInterval, startTime, endTime, green_for_driver)    
            
        elif selectedPerformance == "Comparison volume" or selectedPerformance == "Comparison arrival on green" or selectedPerformance == "Comparison arrival on green ratio":
            image, uuid_name = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList, selectedTimeInterval, startTime, endTime, selectedPerformance, green_for_driver)
            
    else:
        uuid_name = 0

    csv_filename = str(uuid_name) + '.csv'

    request.session['uniqueId'] = csv_filename
    request.session['selectedPerformance'] = selectedPerformance
    request.session['selectedLocationForMap'] = selectedLocation

    context = {'locationNameList': locationNameList,
               'selectedPerformance': selectedPerformance,
               'selectedInfoMeasurement': selectedInfoMeasurement,
               'measuresList': measuresList,
               'timeIntervalList': timeIntervalList,
               'selectedTimeInterval': selectedTimeInterval,
               'selectedLocation': selectedLocation,
               'sgNameList': sgNameList,
               'selectedSgName': selectedSgName,
               'selectedSgNameList': selectedSgNameList, 
               'detectorList': detectorList,
               'detectorListInSelectedLocation': detectorListInSelectedLocation,
               'selectedDetector': selectedDetector,
               'selectedDetectorList': selectedDetectorList,
               'startTimeString': startTime.strftime('%d.%m.%Y %H:%M'),
               'endTimeString': endTime.strftime('%d.%m.%Y %H:%M'),
               'image': image,
               'version_number': version_number,
               'csv_filename': csv_filename,
               'checkboxSelection': checkboxSelection}

    return render(request, 'traffic/index.html', context)


def measuresinfo(request):
    return render(request, 'traffic/measuresinfo.html', "")



def download_data_file(request):
    csv_filename = request.session['uniqueId']
    performance = request.session['selectedPerformance']
    current_time_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return download_file(temp_folder_path + os.sep + csv_filename, performance + current_time_str + '.csv')


def download_user_manual(request):
    file_path = media_folder + "UserManual.pdf"
    with open(file_path, 'rb') as pdf:
        content_type = mimetypes.guess_type(file_path)[0]
        response = HttpResponse(pdf.read(), content_type=content_type)
        response['Content-Disposition'] = 'inline;filename=ImAnalyst_user_manual.pdf'
        return response
    pdf.closed


def maps(request):
    selectedLocation = request.session['selectedLocationForMap']
    map_file = maps_folder + selectedLocation + '.pdf'
    try:
        with open(map_file, 'rb') as pdf:
            content_type = mimetypes.guess_type(map_file)[0]
            response = HttpResponse(pdf.read(), content_type=content_type)
            return response
    except:
        response = HttpResponse('<h1>Sorry, currently no map for this location</h1>')
        return response
