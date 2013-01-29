from django.http import (
    HttpResponse,
    HttpResponseRedirect
)
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.encoding import smart_unicode

from proxy.models import (
    AccessURI,
    CSSReplacer,
    HTMLReplacer,
    ProxyModel
)


def logout(request):
    auth.logout(request)
    #use uri solver!
    return HttpResponseRedirect(reverse('index'))


@login_required
def viewer_home(request):
    if request.POST and u'uri' in request.POST and request.POST[u'uri']:
        uri = request.POST[u'uri']
        p = AccessURI.get_or_create(request.user, uri)[0]

        return HttpResponseRedirect(p.get_cli_access_id())
    else:
        return render_to_response('proxy/viewer_home.html',
                                  context_instance=RequestContext(request))


@login_required
def viewer(request, page_id):
    if request.META['REQUEST_METHOD'] == 'GET':
        text_mime_types = (
            u'text/html', u'application/xhtml+xml',
            u'application/xml', u'text/xml'
        )
        dns_data_list = [{'ipaddr':'198.153.192.40', 'weight':12},
                         {'ipaddr':'8.8.8.8', 'weight':10}]

        access_uri = get_object_or_404(AccessURI, cli_access_id=page_id,
                                       user=request.user)

        proxy = ProxyModel(request, access_uri, dns_data_list)
        status_code, content_type, page_raw_data, encoding = proxy.get_data()

        mime = content_type.split(';')[0]
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

        return response
