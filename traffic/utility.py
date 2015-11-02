import netaddr

class IPFilter(object):
    
    def isIPAllowed(ip, ipRange):
        
        ip = netaddr.IPSet([netaddr.IPAddress(ip)])
        
        for allowedIpSet in ipRange:
            if ip.issubset(allowedIpSet):
                return True
    
        return False        