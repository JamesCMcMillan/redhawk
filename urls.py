from django.conf.urls.defaults import *
from shuttletxt.views import index, accept_event
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
import django_cron
django_cron.autodiscover()

urlpatterns = patterns('',
    (r'^$', index),
    (r'^incoming', accept_event),
    # Example:
    # (r'^redhawk/', include('redhawk.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
