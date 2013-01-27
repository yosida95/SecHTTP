from datetime import timedelta
from random import choice
from string import ascii_letters, digits

import DNS
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class DNSLookupError(Exception):
    pass


class DNSNoResult(Exception):
    pass


class AccessURI(models.Model):
    user = models.ForeignKey(User)
    cli_access_id = models.CharField('number to access uri', max_length=10)
    create_date = models.DateTimeField('date created')
    uri = models.CharField(max_length=500)

    def get_user(self):
        return self.user

    def get_cli_access_id(self):
        return self.cli_access_id

    def get_create_date(self):
        return self.create_date

    def get_uri(self):
        return self.uri

    @classmethod
    def get_or_create(cls, user, uri):
        created = False
        inst = cls.objects.filter(user=user, uri=uri).all()
        if len(inst) > 0:
            inst = inst[0]
        else:
            created = True

            inst = cls(
                user=user, cli_access_id=cls.get_unused_cli_access_id(user),
                create_date=timezone.now(), uri=uri
            )
            inst.save()

        return inst, created

    @classmethod
    def get_unused_cli_access_id(cls, user):
        is_continue = True
        while is_continue:
            cli_access_id = "".join(choice(ascii_letters + digits)
                                    for _ in range(5))
            if cls.objects.filter(cli_access_id=cli_access_id).count() is 0:
                is_continue = False
        else:
            return cli_access_id


class DNSCache(models.Model):
    fqdn = models.CharField(max_length=200, unique=True)
    ip_addr = models.IPAddressField()
    expire_date = models.DateTimeField()

    def get_fqdn(self):
        return self.fqdn

    def get_ip_addr(self):
        return self.ip_addr

    def get_request_date(self):
        return self.request_date

    def update_ip_addr(self, dns_list):
        request = DNSRequest(dns_list)
        try:
            self.ip_addr, ttl = request.lookup(self.fqdn)
        except (DNSLookupError, DNSNoResult):
            return False
        else:
            self.expire_date = timezone.now() + timedelta(seconds=ttl)
            return True

    def is_expired(self):
        return timezone.now() > self.expire_date

    def __unicode__(self):
        return self.fqdn

    @classmethod
    def get_or_create(cls, dns_list, fqdn):
        try:
            inst = cls.objects.get(fqdn=fqdn)
        except cls.DoesNotExist:
            created = True

            inst = cls(fqdn=fqdn)
            inst.update(dns_list)
        else:
            created = False

            if inst.is_expired():
                inst.update(dns_list)

        return inst, created


class DNSRequest(object):

    def __init__(self, dns_list):
        self.dns_list = dns_list

    def lookup(self, hostname):
        results = []
        weights = []
        error_weight = 0

        for dns in self.dns_list:
            try:
                lookup_results = self._request(dns[u'ipaddr'], hostname)
            except DNSLookupError as why:
                if why.args[0] is 3:
                    error_weight += dns[u'weight']
            else:
                for lookup_result in lookup_results:
                    if lookup_result in results:
                        weights[results.index(lookup_result)] += dns[u'weight']
                    else:
                        results.append(lookup_result)
                        weights.append(dns[u'weight'])
        else:
            if len(results) is 0:
                raise DNSNoResult

            max_weight = max(weights)
            if max_weight < error_weight:
                raise DNSLookupError

            return results[weights.index(max_weight)]

    def _request(self, dns, hostname):
        request = DNS.Request(qtype='A', server=dns)
        response = request.req(hostname)
        if response.header[u'status'] != u'NOERROR':
            raise DNSLookupError(response.header[u'rcode'])

        return [(data[u'data'], data[u'ttl']) for data in response.answers]
