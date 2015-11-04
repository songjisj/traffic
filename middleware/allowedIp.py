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
from traffic.utility import IpFilter
import logging


class AllowedIpMiddleware(object):

    def process_request(self, request):
        if settings.DEBUG:
            return None

        try:
            real_ip = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR contains IPs collected from every proxy when
            # request is bypassed.
            # Can be comma-separated list of IP, take just the first one.
            real_ip = real_ip.split(",")[0]
            request.META['REMOTE_ADDR'] = real_ip

        userIp = request.META['REMOTE_ADDR']
        if IpFilter().isIpAllowed(userIp, settings.ALLOWED_NETWORKS):
            return None
        else:
            logging.warn('Permission denied. IP %s does not match to any allowed (configured) network.', userIp)
            raise PermissionDenied
