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
