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

import configparser

config = configparser.RawConfigParser()

#add sections and items 
#section one is for the database configuration on chenlu's laptop
config.add_section('Section1')
config.set('Section1','conn_string',"host='localhost' dbname='tfg-db' user='postgres' password='4097' port='5432'")


#section two is for the database on sunjust's laptop
config.add_section('Section2')
config.set('Section2','conn_string',"host='localhost' dbname='Traffic' user='songji' password='sVYP4f' port='5432'")

with open('config.cfg','wb') as configfile:
    config.write(configfile)