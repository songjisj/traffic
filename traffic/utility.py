import netaddr


class IpFilter(object):

    def isIpAllowed(self, ip, ipRange):
        """
        Check if given ip is a subset of given range.
        :param ip IP address to test
        :param ipRange IP range of acceptable IP addresses
        :return: True if ip is a subset of given range
        """

        ip = netaddr.IPSet([netaddr.IPAddress(ip)])

        for allowedIpSet in ipRange:
            if ip.issubset(allowedIpSet):
                return True

        return False
