from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='proxy/index.html'),
        name='index'),
    url(r'^logout/$', 'proxy.views.logout'),
    url(r'^viewer/$', 'proxy.views.viewer_home'),
    url(r'^viewer/(?P<page_id>[^/?&%#]+)', 'proxy.views.viewer', name=u'viewer'),
)
