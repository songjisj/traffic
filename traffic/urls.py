from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
	url(r'^plot/$', views.plot, name='plot'),
	url(r'^questions/$', views.questions, name='questions'),
	url(r'^index/$', views.index, name='index'),
)
