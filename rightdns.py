#coding:utf-8
#required to install PyDNS
import DNS

class Resolve:
    def request(self,dns_weight_list,fqdn):
        req=DNS.Request(qtype='ANY')
        res_list = [self.send_req(req,dns_weight,fqdn) for dns_weight in dns_weight_list]
        #very ugly
        ipaddr_list=list()
        weight_list=list()
        for res in res_list:
            #if domain is not availavle
            if not res['ipaddr']:
                res['ipaddr']=[False]

            for ipaddr in res['ipaddr']:
                try:
                    same_ipaddr_num = ipaddr_list.index(ipaddr)
                    weight_list[same_ipaddr_num]+=res['weight']
                #if new ipaddr
                except ValueError:
                    ipaddr_list.append(ipaddr)
                    weight_list.append(res['weight'])

        max_weight_num = weight_list.index(max(weight_list))
        print ipaddr_list,weight_list
        return ipaddr_list[max_weight_num]

    def send_req(self,req,dns_weight,fqdn):
        res=req.req(server=dns_weight['dns_ipaddr'],name=fqdn,qtype="A")
        ipaddr=[answer['data'] for answer in res.answers]
        return {'ipaddr':ipaddr,'weight':dns_weight['weight']}

#resolver = Resolve()
#print resolver.request([{'dns_ipaddr':'210.171.161.7','weight':15},{'dns_ipaddr':'198.153.192.40','weight':12},{'dns_ipaddr':'8.8.8.8','weight':10}],'www.e-ontap.com')
