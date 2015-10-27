from mysite.settings_template import *

DEBUG = TEMPLATE_DEBUG = False

#TODO: Figure out how to get these by different target env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'TrafficFlow',
        'OPTIONS': {
            'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
        },
        'USER': 'TrafficFlowReader',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

