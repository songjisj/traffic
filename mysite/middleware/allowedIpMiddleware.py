from django.conf import settings
from django.http import Http404
import re

class AllowedIpMiddleware(object):
    def process_request(self, request):
        userIp = request.META['REMOTE_ADDR']
        if settings.DEBUG:
            return None
        if userIp in settings.INTERNAL_IPS:
            return None
        for allowedIpRegEx in settings.INTERNAL_IPS:
            isMatching = re.compile(allowedIpRegEx).match(userIp)
            if isMatching:
                return None
        raise Http404