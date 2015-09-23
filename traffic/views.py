from django.shortcuts import render
from django.http import HttpResponse
from matplotlib import pylab
from pylab import *
import PIL
import PIL.Image
import StringIO
from .models import TfRaw,Controller,ControllerConfigDet,ControllerConfigSg
from analysis import rowNumber
from analysis import get_green_time, get_sg_config_in_one, get_det_config_in_one_sg,get_capacity,get_queue_length,get_green_time_2,get_capacity_2,get_maxCapacity,get_arrival_on_green

from .forms import ControlForm
from .forms import ContactForm
import dateutil.parser
from datetime import datetime
from pytz import timezone
import datetime
import csv 
#import iso8601


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
    selectedDetector = ""
    startTimeString =""
    timeIntervalList =["5m","10m","20m","30m","60m"] 
    #Select performance 
    try:
        selectedPerformance = request.POST['performance']
    except(KeyError):
        selectedPerformance = "greenDuration" 
    
    
    try:
        startTime = request.POST['startdate']   
    except(KeyError):
        startTime = "2015-07-08 13:00:24+03"   
        
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
        sgNameDict = get_sg_config_in_one(selectedLocation,"")  
        sgNameList = sgNameDict.values()
    
    try:
        selectedSgName = request.POST['signalGroup']
    except(KeyError):
        if sgNameList :
            selectedSgName = sgNameList[0]
    
    #Select detector
    if selectedSgName and selectedLocation :
        detectorDict = get_det_config_in_one_sg(selectedLocation, selectedSgName, "") 
        detectorList = detectorDict.values() 
    
    try: 
        selectedDetector = request.POST['detector']
    except(KeyError):
        if detectorList :
            selectedDetector = detectorList[0]
            
    try:
        selectedTimeInterval = request.POST['timeInterval']
    except(KeyError):
        if timeIntervalList:
            selectedTimeInterval = timeIntervalList[0]
 
    form = ContactForm(request.POST)
        
    startTimeString = request.POST.get('starttime',"")
    endTimeString = request.POST.get('endtime',"")
    
    helsinkiTimezone = timezone('Europe/Helsinki')
    timeZone = datetime.datetime.now(helsinkiTimezone).strftime('%z')
    
    measuresList = ["capacity","greenDuration","queueLength","activeGreen","maximumCapacity","arrivalOnGreenPercent","volume","arrivalOnGreenRatio"] 
    
    
    #display csv file 
    fileReader = csv.reader("traffic/static/traffic/result.csv", delimiter=',')
    lineNum = 0  #initialize linenumber
    
    context = {'locationNameList':locationNameList, 
               'selectedPerformance':selectedPerformance,
               'measuresList':measuresList,
               'timeIntervalList':timeIntervalList,
               'selectedTimeInterval':selectedTimeInterval,
               'selectedLocation':selectedLocation,               
               'sgNameList':sgNameList,
               'selectedSgName':selectedSgName,
               'detectorList':detectorList,
               'selectedDetector':selectedDetector,
               'startTimeString':startTimeString,
               'startTimeString':startTimeString,
               'endTimeString':endTimeString,
               'fileReader':fileReader,
               'lineNum':lineNum,
               'form':form}    
    
    refreshType = request.POST.get('refreshType',"")
    
    if refreshType == "Plot" and startTimeString and endTimeString :
        startTimeStringTimeZone = startTimeString + timeZone
        endTimeStringTimeZone = endTimeString + timeZone 
        if selectedPerformance == "greenDuration":
            get_green_time_2(selectedLocation, "",startTimeStringTimeZone, endTimeStringTimeZone)   
        elif selectedPerformance =="capacity":
            get_capacity_2(selectedLocation,"",selectedSgName,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance == "queueLength":
            get_queue_length(selectedLocation,"",selectedSgName,selectedDetector,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance == "activeGreen":
            get_green_time(selectedLocation, "", selectedSgName, startTimeStringTimeZone, endTimeStringTimeZone)
        elif selectedPerformance =="maximumCapacity":
            get_maxCapacity(selectedLocation,selectedSgName,selectedDetector,"",selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone)
        elif selectedPerformance =="arrivalOnGreenPercent":
            get_arrival_on_green(selectedLocation,"",selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)
        elif selectedPerformance =="volume":
            get_arrival_on_green(selectedLocation,"",selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)
        elif selectedPerformance =="arrivalOnGreenRatio":
            get_arrival_on_green(selectedLocation,"",selectedSgName,selectedDetector,selectedTimeInterval,startTimeStringTimeZone,endTimeStringTimeZone,selectedPerformance)        
    
    

    #return HttpResponse(green_example, content_type="image/png")
     
    return render(request, 'traffic/index.html', context)

def data(request):
    control_form = ControlForm(request.POST)
    if control_form.is_valid():
        
        return render(request, 'data.html',{'control_form':control_form}) 
        

def plot(request):
    x = [1,2,3,4]
    y = [20, 21, 20.5, 20.8]
    plt.plot(x, y)

    buffer = StringIO.StringIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.fromstring("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()
    return HttpResponse(buffer.getvalue(), content_type="image/png")
def measuresinfo(request):
    
    return render(request,'traffic/measuresinfo.html',"")

def maps(request):
    selectedLocation = ""
    try:
        selectedLocation = somevalue #I have no idea 
    except(KeyError):
        selectedLocation = "TRE303" 
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

