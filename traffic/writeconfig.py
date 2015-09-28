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