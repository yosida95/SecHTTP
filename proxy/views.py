from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound
)
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.encoding import smart_unicode

from proxy.models import (
    URIManager,
    CSSReplacer,
    HTMLReplacer,
    ProxyModel
)
import time


def logout(request):
    auth.logout(request)
    #use uri solver!
    return HttpResponseRedirect(reverse(u'index'))


@login_required
def viewer_home(request):
    if request.POST and u'uri' in request.POST and request.POST[u'uri']:
        uri = request.POST[u'uri']
        urimanager = URIManager()
        referer = u''
        pageid = urimanager.encode(uri, int(time.time()),
                                   request.user.username, referer)

        return HttpResponseRedirect(pageid)
    else:
        return render_to_response(u'proxy/viewer_home.html',
                                  context_instance=RequestContext(request))


@login_required
def viewer(request, page_id):
    if request.META[u'REQUEST_METHOD'] == u'GET':
        text_mime_types = (
            u'text/html', u'application/xhtml+xml',
            u'application/xml', u'text/xml'
        )
        dns_data_list = [{u'ipaddr': u'198.153.192.40', u'weight': 12},
                         {u'ipaddr': u'8.8.8.8', u'weight': 10}]

        urimanager = URIManager()
        access_uri, make_time, make_user, referer = urimanager.decode(page_id)

        if make_user != request.user.username:
            return HttpResponseNotFound()

        proxy = ProxyModel(request, access_uri, dns_data_list)
        status_code, content_type, page_raw_data, encoding = proxy.get_data()

        mime = content_type.split(u';')[0]
        if mime in text_mime_types:
            html_replacer = HTMLReplacer(request.user, proxy.get_request_uri())
            body = html_replacer.replace(
                smart_unicode(page_raw_data, encoding=encoding)
            )

            content_type = u'%s; charset=utf-8' % mime
        elif mime == u'text/css':
            css_replacer = CSSReplacer(request.user, proxy.get_request_uri())
            body = css_replacer.replace(
                smart_unicode(page_raw_data, encoding=encoding)
            )

            content_type = u'%s; charset=utf-8' % mime
        else:
            body = page_raw_data

        response = HttpResponse(body, status=status_code)
        response[u'Content-Type'] = content_type
        response[u'Cache-Control'] = u'no-cache'
        response[u'Pragma'] = u'no-cache'
        response[u'Referer'] = referer

        return response
