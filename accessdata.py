#coding:utf-8
import requests
from urlparse import urlparse


class AccessData:
    #path:"/hoho/ho.png"
    def get(self,ipaddr,base_uri,ua,cookie=None,referer=None):

        urldat = urlparse(base_uri)
        scheme = urldat.scheme
        server_dir = urldat.path
        if not server_dir:
            server_dir = '/'
        path = server_dir+'?'+urldat.query
        port = urldat.port
        fqdn = urldat.hostname
        if not port:
            uri = '%s://%s%s'%(scheme,ipaddr,path)
        else:
            uri = '%s://%s:%s%s'%(scheme,ipaddr,port,path)

        headers = dict()
        headers["User-Agent"]=ua
        if referer:
            headers["Referer"]=referer

        if scheme=='http':
            headers["Host"]=fqdn
            res_data = requests.get(uri,headers=headers,cookies=cookie,allow_redirects=False)
        elif scheme=='https':
            res_data = requests.get(base_uri,headers=headers,cookies=cookie,verify=True,allow_redirects=False)
        else:
            raise WrongSchemeError

        try:
            new_uri = res_data.headers['location']
            if new_uri!=base_uri:
                change_uri=True
            else:
                change_uri=False
        except KeyError:
            new_uri=base_uri
            change_uri=False

        data = res_data.text
        status_code = res_data.status_code
        res_cookie = res_data.cookies
        encoding = res_data.encoding
        content_type = res_data.headers['Content-Type']
        
        return data,status_code,res_cookie,encoding,content_type,new_uri,change_uri

class WrongSchemeError(Exception):
    def __init__(self,name):
        self.name = name
    def __str__(self):
        return 'Requested scheme(\'%s\') was not http or https'%(self.name)

#access = AccessData()
#print access.get("74.125.235.184","http","/","google.co.jp","Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",[{'ipaddr':'198.153.192.40','weight':12},{'ipaddr':'8.8.8.8','weight':10}])
