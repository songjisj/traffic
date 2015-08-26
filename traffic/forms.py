from django import forms
from .models import TfRaw,Controller,ControllerConfigDet,ControllerConfigSg 

class ControlForm(forms.Form):
    intersection_label =forms.CharField(label = 'Intersection') 
    intersection=forms.ChoiceField(choices=('1','2','3'), required=True, widget=forms.Select, 
                                  label=None, 
                                  initial=None, 
                                  help_text='')
    performance_label = forms.CharField(label = 'Performance measures')
    #performance=forms.ChoiceField
    #signalGroup=forms.ChoiceField()
    #stratTime=forms.DateTimeField 
    #endTime=forms.DateTimeField
    
    
class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)    