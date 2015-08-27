from django.shortcuts import render
from django.http import HttpResponse
from matplotlib import pylab
from pylab import *
import PIL
import PIL.Image
import StringIO
from .models import TfRaw,Controller,ControllerConfigDet,ControllerConfigSg
from analysis import rowNumber
from analysis import get_green_time, get_sg_config_in_one, get_det_config_in_one
import time
from .forms import ControlForm
from .forms import ContactForm

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
    locationNameList = []
    selectedLocation = ''
    
    #get_green_time("'TRE303'", "",  'A',"'2015-07-08 13:00:24+03'", "'2015-07-08 14:00:24+03'") 
    
    #Select location
    locationObjectList = Controller.objects.all() 
    for location in locationObjectList:
        locationNameList.append(location.cname)
      
    try:
        selectedLocation = request.POST['location']   
    except(KeyError):
        selectedLocation = "TRE303"
        
    #Select signalGroup
    if selectedLocation:
        sgNameDict = get_sg_config_in_one("'"+selectedLocation+"'","")  
        sgNameList = sgNameDict.values()
    
    try:
        selectedSgName =request.POST['signalGroup']
    except(KeyError):
        if sgNameList :
            selectedSgName = sgNameList[0]
    
    #Select detector
    if selectedSgName and selectedLocation :
        detectorDict = get_det_config_in_one("'"+selectedLocation+"'", selectedSgName, "") 
        detectorList = detectorDict.values() 
    
    try: 
        selectedDetector = request.POST['detector']
    except(KeyError):
        if detectorList :
            selectedDetector = detectorList[0]
        
    form = ContactForm(request.POST)
    
    context = {'locationNameList':locationNameList, 
               'selectedLocation':selectedLocation,               
               'sgNameList':sgNameList,
               'selectedSgName':selectedSgName,
               'detectorList':detectorList,
               'selectedDetector':selectedDetector,
               'form':form}
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