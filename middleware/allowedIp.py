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

from django.conf import settings
from django.core.exceptions import PermissionDenied
from traffic.process import isIpAllowed

class AllowedIpMiddleware(object):

    def process_request(self, request):
        if settings.DEBUG:
            return None        
        userIp = request.META['REMOTE_ADDR']
        if isIpAllowed(userIp, settings.ALLOWED_NETWORKS):
            return None
        else:
            raise PermissionDenied 

