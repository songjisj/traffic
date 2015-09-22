from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
	url(r'^plot/$', views.plot, name='plot'),
	url(r'^questions/$', views.questions, name='questions'),
	url(r'^index/$', views.index, name='index'),
        url(r'^measuresinfo',views.measuresinfo,name='measuresinfo'),
        url(r'^data/$', views.data, name='data'),   
        url(r'^../static/traffic/result.csv',views.download_data_file),
)
