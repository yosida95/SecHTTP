#coding:utf-8
#required to install PyDNS
import DNS

class Resolve:
    def request(self,dns_data_list,fqdn):
        #TODO:Request with TCP
        ipaddr_list = list()
        weight_list=list()
        error_weight = 0
        ng_ipaddr = '198.153.192.3'

        for dns_data in dns_data_list:
            try:
                new_ipaddr_list = self.send_req(dns_data['ipaddr'],fqdn)
            except DNS.Base.ServerError as e:
                if e.rcode==3:
                    error_weight+=dns_data['weight']
            except DNS.Base.TimeoutError:
                raise NoServerError
                
            else:
                for new_ipaddr in new_ipaddr_list:
                    try:
                        same_ipaddr_index = ipaddr_list.index(new_ipaddr)
                    except ValueError:
                        if new_ipaddr==ng_ipaddr:
                            continue
                        ipaddr_list.append(new_ipaddr)
                        weight_list.append(dns_data['weight'])
                    else:
                        weight_list[same_ipaddr_index]+=dns_data['weight']

        try:
            max_weight_num = weight_list.index(max(weight_list))
            if max_weight_num<error_weight:
                raise NoFQDNError
        except ValueError:
            raise NoFQDNError
        max_ipaddr = ipaddr_list[max_weight_num]
        return max_ipaddr

    def send_req(self,dns_addr,fqdn):
        DNS.defaults['server']=[dns_addr]
        ipaddr=DNS.dnslookup(fqdn,'A')
        return ipaddr

class NoServerError(Exception):
    def __str__(self):
        return "No DNS server found!"
class NoFQDNError(Exception):
    def __str__(self):
        return "No such FQDN found!"
    

#resolver = Resolve()
#print resolver.request([{'ipaddr':'198.153.192.4','weight':12},{'ipaddr':'8.8.8.4','weight':10}],'www.google.co.jp')
