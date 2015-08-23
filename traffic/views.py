from django.shortcuts import render
from django.http import HttpResponse
from matplotlib import pylab
from pylab import *
import PIL
import PIL.Image
import StringIO
from .models import TfRaw
from temp import rowNumber
from temp import get_green_time

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
    rows = rowNumber()
    get_green_time("'TRE303'", "",  'A',"'2015-07-08 13:00:24+03'", "'2015-07-08 14:00:24+03'")    
    try:
        rows = request.POST['choice']
    except (KeyError):
        rows = 2
    trafficDataList = TfRaw.objects.order_by('row_id')[:rows]
    context = {'trafficDataList': trafficDataList}
    #return HttpResponse(green_example, content_type="image/png")
    return render(request, 'traffic/index.html', context)

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