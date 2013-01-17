#coding:utf-8
import requests
from urlparse import urlparse
import rightdns


class AccessData:
    #path:"/hoho/ho.png"
    def get(self,ipaddr,proto,path,fqdn,ua,dns_data_list,cookie=None,referer=None):

        uri = "%s://%s%s"%(proto,ipaddr,path)

        headers = dict()
        headers["User-Agent"]=ua
        headers["Host"]=fqdn
        if referer:
            headers["Referer"]=referer

        #ugly...
        status_code=301
        while status_code == 301 or status_code==302 or status_code==303 or status_code==307:
            res_data = requests.get(uri,headers=headers,cookies=cookie,verify=True,allow_redirects=False)
            status_code = res_data.status_code
            try:
                new_uri = res_data.headers['location']
                host = urlparse(new_uri).hostname
                path = urlparse(new_uri).path
                headers['Host'] = host
                resolver = rightdns.Resolve()
                ipaddr = resolver.request(dns_data_list,host)
                uri = "%s://%s%s"%(proto,ipaddr,path)

            except (ValueError,AttributeError):
                break

        data = res_data.text
        status_code = res_data.status_code
        res_cookie = res_data.cookies
        encoding = res_data.encoding
        content_type = res_data.headers['Content-Type']
        now_uri = uri
        
        return data,status_code,res_cookie,encoding,content_type,now_uri


#access = AccessData()
#print access.get("74.125.235.184","http","/","google.co.jp","Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",[{'ipaddr':'198.153.192.40','weight':12},{'ipaddr':'8.8.8.8','weight':10}])
