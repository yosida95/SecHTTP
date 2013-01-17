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

        session = requests.Session()
        session.max_redirects=10

        res_data = session.get(uri,headers=headers,cookies=cookie,verify=True,allow_redirects=True)
        now_uri = res_data.url

        data = res_data.text
        status_code = res_data.status_code
        res_cookie = res_data.cookies
        encoding = res_data.encoding
        content_type = res_data.headers['Content-Type']
        
        return data,status_code,res_cookie,now_uri,encoding,content_type


#access = AccessData()
#print access.get("192.168.3.8","http","/","192.168.3.2","Mozilla/4.0 (Compatible; MSIE 6.0; Windows NT 5.1;)")
