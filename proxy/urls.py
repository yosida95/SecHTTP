from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='proxy/index.html'),
        name='index'),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^logout/', 'proxy.views.logout'),
    url(r'^viewer/$', 'proxy.views.viewer_home'),
    url(r'^viewer/(?P<page_id>\w+)/$', 'proxy.views.viewer'),
)
