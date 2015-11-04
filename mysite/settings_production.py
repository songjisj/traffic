from mysite.settings_template import *

DEBUG = TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'TrafficFlow',
        'OPTIONS': {'options': '-c search_path=public',
                    'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED
                    },
        'USER': 'TrafficFlowReader',
        'PASSWORD': 'r34d3r',
        'HOST': '10.10.250.65',
        'PORT': '5432',
    }
}

STATIC_URL = '/imanalyst/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/opt/vassals/ImAnalyst/traffic/static/',
)

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '10.10.250.75',
]

ALLOWED_NETWORKS = [IPSet(['127.0.0.0/8']),      # loopback addresses
                    IPSet(['10.10.20.0/28']),    # Imtech VPN network
                    ]

IP_RANGE_DICT = {'FullAccessUser': [[IPSet(['10.10.20.0/24']), ], ['']],
                 'RegionalUser1': [[IPSet(['10.10.20.0/28']), ], ['oulu']],
                 'RegionalUser2': [[IPSet(['10.10.20.0/28']), ], ['tre', 'nok']]
                 }
