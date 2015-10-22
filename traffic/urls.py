from django.conf.urls import patterns, url
from traffic.views import *

urlpatterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^index/$', index, name='index'),
    url(r'^measuresinfo', measuresinfo,name='measuresinfo'),
    url(r'^maps', maps,name='maps'),
    url(r'^data/$', data, name='data'),   
    url(r'^../static/traffic/result.csv', download_data_file),
)
