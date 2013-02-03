from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^',include('proxy.urls')),
    url(r'^accounts/',include('registration.backends.simple.urls')),
    url(r'^admin/',include(admin.site.urls)),
)
