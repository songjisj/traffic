from django.shortcuts import render
from django.http import HttpResponse
from .models import TfRaw,Controller,ControllerConfigDet,ControllerConfigSg

from traffic.analysis import *
from .forms import ControlForm
from .forms import ContactForm
import dateutil.parser
from pytz import timezone
import datetime
import csv


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

def questions(request):
    trafficDataList = TfRaw.objects.order_by('-row_id')[:2]
    output = ', '.join([p.grint for p in trafficDataList])
    return HttpResponse(output)

def index(request):
    selectedPerformance = ""
    locationNameList = []
    selectedLocation = ""
    sgNameList = [] 
    selectedSgName = ""
    detectorList = []
    selectedDetectorList = []
    selectedDetector = ""
    startTimeString =""
    timeIntervalList =["5","10","20","30","60"] 
    #Select performance 
    try:
        selectedPerformance = request.POST['performance']
    except(KeyError):
        selectedPerformance = "greenDuration"  
        
    #Select location
    locationObjectList = Controller.objects.all() 
    for location in locationObjectList:
        locationNameList.append(location.cname)
    locationNameList = sorted(locationNameList)
    
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
        if sgNameList :
            selectedSgName = sgNameList[0]
    
    #Select detector
    if selectedSgName and selectedLocation :
        detectorDict = get_det_config_in_one_sg(selectedLocation, selectedSgName) 
        detectorList = sorted(list(detectorDict.values()))
    
    try: 
        selectedDetector = request.POST['detector']
    except(KeyError):
        if detectorList :
            selectedDetector = detectorList[0]
    
    # Select multiple detectors  
    if selectedLocation:
        detectorDictInSelectedLocation = get_det_in_one_location(selectedLocation)
        detectorListInSelectedLocation = sorted(list(detectorDictInSelectedLocation.values())) 

    try:
        selectedDetectorList = request.POST.getlist('detectors[]')  
    except(KeyError):
        if detectorListInSelectedLocation :
            selectedDetectorList =detectorListInSelectedLocation[0:1] 
     
    # Select time interval         
    try:
        selectedTimeInterval = request.POST['timeInterval']
    except(KeyError):
        if timeIntervalList:
            selectedTimeInterval = timeIntervalList[0]
 
    form = ContactForm(request.POST)
    


    # select start and end time   
    startTimeString = request.POST.get('starttime',"")
    endTimeString = request.POST.get('endtime',"")
    #print(startTimeString)
    #print(endTimeString)
    helsinkiTimezone = timezone('Europe/Helsinki')
    timeZone = datetime.datetime.now(helsinkiTimezone).strftime('%z')
    #get current datetime
    current_datetime = datetime.datetime.now(helsinkiTimezone).strftime('%d-%m-%Y %H:%M')  
    print((current_datetime)) 
    
    measuresList = ["Saturation_flow_rate","Percent_of_green_duration","Green_duration","Queue_length","Active_green",
                    "Maximum_capacity","Arrival_on_green_percent","Volume","Arrival_on_green_ratio","Comparison_volume",
                    "Comparison_arrival_on_green","Comparison_arrival_on_green_ratio","Green_time_in_interval"] 
    
    
    #display csv file 
    fileReader = csv.reader("traffic/static/traffic/result.csv", delimiter=',')
    lineNum = 0  #initialize linenumber
    
    
    
    refreshType = request.POST.get('refreshType',"")
    image = ""
    if refreshType == "Plot" and startTimeString and endTimeString :
        startTimeStringTimeZone = startTimeString + timeZone
        endTimeStringTimeZone = endTimeString + timeZone 
        if selectedPerformance == "Green_duration":
            image = get_green_time_2(selectedLocation,startTimeStringTimeZone, endTimeStringTimeZone,selectedPerformance)   
        elif selectedPerformance == "Percent_of_green_duration":
            image = get_green_time_2(selectedLocation,startTimeStringTimeZone, endTimeStringTimeZone,selectedPerformance)           
        elif selectedPerformance =="Saturation_flow_rate":
            image = get_saturation_flow_rate(selectedLocation,selectedSgName,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance == "Queue_length":
            image = get_queue_length(selectedLocation,selectedSgName,selectedDetector,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance == "Active_green":
            image = get_green_time(selectedLocation, selectedSgName, startTimeStringTimeZone, endTimeStringTimeZone)
        elif selectedPerformance =="Maximum_capacity":
            image = get_maxCapacity(selectedLocation,selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance =="Arrival_on_green_percent":
            image = get_arrival_on_green(selectedLocation,selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)
        elif selectedPerformance =="Volume":
            image = get_volume_lanes(selectedLocation,selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance =="Arrival_on_green_ratio":
            image = get_arrival_on_green(selectedLocation,selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)        
        elif selectedPerformance =="Comparison_volume":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)
        elif selectedPerformance =="Comparison_arrival_on_green":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)
        elif selectedPerformance =="Comparison_arrival_on_green_ratio":
            image = get_compared_arrival_on_green_ratio(selectedLocation, selectedDetectorList,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance) 
        elif selectedPerformance == "Green_time_in_interval":
            image = get_green_time_in_interval(selectedLocation, selectedTimeInterval, 
                                              startTimeStringTimeZone, 
                                              endTimeStringTimeZone)
    context = {'locationNameList':locationNameList, 
               'selectedPerformance':selectedPerformance,
               'measuresList':measuresList,
               'timeIntervalList':timeIntervalList,
               'selectedTimeInterval':selectedTimeInterval,
               'selectedLocation':selectedLocation,               
               'sgNameList':sgNameList,
               'selectedSgName':selectedSgName,
               'detectorList':detectorList,
               'detectorListInSelectedLocation':detectorListInSelectedLocation,
               'selectedDetector':selectedDetector,
               'selectedDetectorList':selectedDetectorList, 
               'startTimeString':startTimeString,
               'endTimeString':endTimeString,
               'current_datetime':current_datetime,
               'fileReader':fileReader,
               'lineNum':lineNum,
               'form':form,
               'image':image}    
    #return HttpResponse(green_example, content_type="image/png")
     
    return render(request, 'traffic/index.html', context)

def data(request):
    control_form = ControlForm(request.POST)
    if control_form.is_valid():
        
        return render(request, 'data.html',{'control_form':control_form}) 

def measuresinfo(request):
    
    return render(request,'traffic/measuresinfo.html',"")

def maps(request):
    selectedLocation = request.POST.get('selectedLocatioForMap',"TRE303")
    context = {'selectedLocation':selectedLocation}
    return render(request, 'traffic/maps.html', context)

def download_data_file(request):
    import os,tempfile,zipfile
    from django.core.servers.basehttp import FileWrapper
    from django.conf import settings
    import mimetypes
    
    filename = "traffic/static/traffic/result.csv"
    download_name = "result.csv"
    wrapper = FileWrapper(open(filename))
    content_type = mimetypes.guess_type(filename)[0]
    response = Httpresponse(wrapper,content_type=content_type)
    response['Content-length'] = os.path.getsize(filename)
    response['Content-Disposition'] ="attachment;filename=%s"%download_name
    return response 

