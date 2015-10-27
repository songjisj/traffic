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


import unittest
from django.conf import settings
from middleware.allowedIp import AllowedIpMiddleware


class TestAllowedIpMiddleware(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.DEBUG = False

    def setUp(self):
        self.mw = AllowedIpMiddleware()

    def test_passDebug(self):
        settings.DEBUG = True
        self.assertTrue(self.mw.isIpAllowed('10.10.0.1'), 'With DEBU=True every IP should be accepted.')
        settings.DEBUG = False
        self.assertFalse(self.mw.isIpAllowed('10.10.0.1'))

    def test_Localhost(self):
        self.assertTrue(self.mw.isIpAllowed('127.0.0.1'), 'Localhost should be accepted.')

    def test_Unknown(self):
        self.assertFalse(self.mw.isIpAllowed('19.3.2.1'), '"19.3.2.1" should not be accepted.')

if __name__ == "__main__":
    unittest.main()
