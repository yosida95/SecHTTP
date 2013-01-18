from django.http import HttpResponseRedirect,HttpResponse
from django.contrib import auth
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response,get_object_or_404
from django.contrib.auth.decorators import login_required
from proxy.models import AccessURI,DNSCache
from django.utils import timezone
from django.utils.encoding import smart_unicode
from django.template import RequestContext
from urlparse import urlparse
import accessdata
import rightdns
import page_id_maker
import validdat

def logout(request):
    auth.logout(request)
    #use uri solver!
    return HttpResponseRedirect(reverse('index'))

@login_required
def viewer_home(request):
    if request.META['REQUEST_METHOD'] == 'GET':
        return render_to_response('proxy/viewer_home.html',context_instance=RequestContext(request))

    elif request.META['REQUEST_METHOD'] == 'POST':
        uri = request.POST['uri']
        cli_access_id = page_id_maker.make()
        fqdn=urlparse(uri).hostname
        p = AccessURI(user=request.user,cli_access_id=cli_access_id,create_date=timezone.now(),fqdn=fqdn,uri=uri)
        p.save()
        return HttpResponseRedirect(cli_access_id)

@login_required
def viewer(request,page_id):
    if request.META['REQUEST_METHOD']=='GET':

        dns_data_list = [{'ipaddr':'198.153.192.40','weight':12},{'ipaddr':'8.8.8.8','weight':10}]
        data = get_object_or_404(AccessURI,cli_access_id=page_id,user=request.user)
        new_uri = data.uri
        
        access=accessdata.AccessData()
        ua=request.META['HTTP_USER_AGENT']

        status_code = None
        while status_code==None or status_code==301 or status_code==302 or status_code==303:
            #use cache if availavle
            try:
                cache_obj = DNSCache.objects.filter(fqdn=data.fqdn).order_by('request_date')[0]
                ip_addr = cache_obj.ip_addr
            except IndexError:
                resolver=rightdns.Resolve()
                ip_addr = resolver.request(dns_data_list,data.fqdn)
                cache_w_obj = DNSCache(fqdn=data.fqdn,ip_addr=ip_addr,request_date=timezone.now())
                cache_w_obj.save()

            uri = new_uri
            page_raw_data,status_code,cookiejar,encoding,content_type,new_uri = access.get(ip_addr,uri,ua,dns_data_list)

        mime = content_type.split(';')[0]
        if mime=='text/html':
            page_data = smart_unicode(page_raw_data,encoding=encoding)

            valid = validdat.ValidDat()
            validated_page_data,page_id_lst,page_uri_lst = valid.valid(page_data,uri)

            for num in range(len(page_id_lst)):
                add_addr = page_uri_lst[num]
                addaddr_fqdn=urlparse(add_addr).hostname

                uri_obj = AccessURI(user=request.user,cli_access_id=page_id_lst[num],create_date=timezone.now(),uri=add_addr,fqdn=addaddr_fqdn)
                uri_obj.save()

            response = HttpResponse(validated_page_data,status=status_code)
            response['Content-Type']=mime+'; charset=utf-8'
 
        else:
            validated_page_data = page_raw_data
            response = HttpResponse(validated_page_data,status=status_code)
            response['Content-Type']=content_type
 
        return response

