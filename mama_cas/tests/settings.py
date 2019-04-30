DEBUG = False
TEMPLATE_DEBUG = DEBUG

TIME_ZONE = 'UTC'
USE_TZ = True

SECRET_KEY = 'khhmbe6*m$ix_h0t%)@$4mh%a2)2f=4-fyv*-=^6=m**p+=f7n'

ROOT_URLCONF = 'mama_cas.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

MIDDLEWARE_CLASSES = MIDDLEWARE

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'mama_cas',
)

MAMA_CAS_SERVICES = [
    {
        'SERVICE': r'https?://.+\.example\.com',
        'PROXY_ALLOW': True,
        'PROXY_PATTERN': r'https://.+\.example\.com',
        'CALLBACKS': [
            'mama_cas.callbacks.user_name_attributes',
        ],
        'LOGOUT_ALLOW': True,
        'LOGOUT_URL': 'https://example.com/logout',
    },
    {
        'SERVICE': 'http://example.com',
        'PROXY_ALLOW': False,
        'LOGOUT_ALLOW': False,
    },
    {
        'SERVICE': 'exception',
        'CALLBACKS': [
            'mama_cas.tests.callbacks.raise_exception',
        ],
    },
]
