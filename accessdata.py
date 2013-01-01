#coding:utf-8
import requests

class AccessData:
    #path:"/hoho/ho.png"
    def get(self,ipaddr,proto,path,fqdn,ua,cookie=None,referer=None):

        uri = "%s://%s%s"%(proto,ipaddr,path)

        headers = dict()
        headers["User-Agent"]=ua
        headers["Host"]=fqdn
        if referer:
            headers["Referer"]=referer

        res_data = requests.get(uri,headers=headers,cookies=cookie,verify=True)
        data = res_data.text
        status_code = res_data.status_code
        res_cookie = res_data.cookies
        now_uri = res_data.url
        encoding = res_data.encoding
        content_type = res_data.headers['Content-Type']
        
        return data,status_code,res_cookie,now_uri,encoding,content_type

    #almost same function!!! ugly!!!!
    def post(self,ipaddr,proto,path,fqdn,ua,payload,cookie=None,referer=None):

        uri = "%s://%s%s"%(proto,ipaddr,path)

        headers = dict()
        headers["User-Agent"]=ua
        headers["Host"]=fqdn
        if referer:
            headers["Referer"]=referer

        res_data = requests.get(uri,headers=headers,cookies=cookie,data=payload,verify=True)
        data = res_data.text
        status_code = res_data.status_code
        res_cookie = res_data.cookies
        now_uri = res_data.url
        
        return data,status_code,res_cookie,now_uri


#access = AccessData()
#print access.get("192.168.3.8","http","/","192.168.3.2","Mozilla/4.0 (Compatible; MSIE 6.0; Windows NT 5.1;)")
