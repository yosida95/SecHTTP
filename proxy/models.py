import logging
from datetime import timedelta
from random import choice
from string import ascii_letters, digits
from urlparse import (
    urlparse,
    urlunparse,
    urljoin
)

import cssutils
import DNS
import requests
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from Crypto.Cipher import ARC4
from Crypto import Random
from Crypto.Hash import SHA512
import base64
import cPickle
import zlib
import time

from crypto_data import crypto_key


class DNSLookupError(Exception):
    pass


class DNSNoResult(Exception):
    pass


class WrongSchemeError(Exception):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return u'Requested scheme(\'%s\') was not http or https' % (self.name)


class URIManager:
    def encode(self, uri, time, username, referer):
        key = crypto_key
        binary_proto = 2

        accessdata = {u'u': uri, u'n': username, u't': time, u'r': referer}
        accessdata_str = cPickle.dumps(accessdata, binary_proto)
        encrypted_accessdata, nonce = self.encrypt(accessdata_str, key)
        data_list = {u'd': encrypted_accessdata, u'n': nonce}
        data_list_str = cPickle.dumps(data_list)
        compressed_data = zlib.compress(data_list_str)
        encoded_data = base64.urlsafe_b64encode(compressed_data)

        return encoded_data

    def decode(self, encoded_data):
        key = crypto_key
        binary_proto = 2

        compressed_data = base64.urlsafe_b64decode(
            encoded_data.encode(u'ascii') if isinstance(encoded_data, unicode)
            else encoded_data
        )
        data_list_str = zlib.decompress(compressed_data)
        data_list = cPickle.loads(data_list_str)
        accessdata_str = self.decrypt(data_list[u'd'], key, data_list[u'n'])
        accessdata = cPickle.loads(accessdata_str)

        uri = accessdata[u'u']
        username = accessdata[u'n']
        time = accessdata[u't']
        referer = accessdata[u'r']

        return uri, time, username, referer

    def encrypt(self, text, key):
        nonce = Random.new().read(8)
        tempkey = SHA512.new(key + nonce).digest()
        cipher = ARC4.new(tempkey)
        encrypted_text = cipher.encrypt(text)
        return encrypted_text, nonce

    def decrypt(self, encrypted_text, key, nonce):
        tempkey = SHA512.new(key + nonce).digest()
        cipher = ARC4.new(tempkey)
        text = cipher.decrypt(encrypted_text)
        return text


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
        request = DNS.Request(qtype='A', server=dns.encode(u'utf8'))
        response = request.req(hostname.encode(u'utf8'))
        if response.header[u'status'] != u'NOERROR':
            raise DNSLookupError(response.header[u'rcode'])

        return [(data[u'data'], data[u'ttl']) for data in response.answers]


class URIReplacer(object):

    def __init__(self, user, base_uri):
        self.user = user
        self.base_uri = base_uri

    def get_access_uri(self, uri):
        urimanager = URIManager()
        access_uri = urimanager.encode(
            urljoin(self.base_uri, uri), int(time.time()), self.base_uri
        )
        return access_uri


class HTMLReplacer(URIReplacer):

    def replace(self, html):
        soup = BeautifulSoup(html)

        soup = self.remove_tags(soup, u'script')
        soup = self.remove_tags(soup, u'object')
        soup = self.remove_tags(soup, u'iframe')

        self.unwrap_tag(soup, u'noscript')

        self.replace_tag_attrs(soup, u'a', [u'href'])
        self.replace_tag_attrs(soup, u'link', [u'href'])
        self.replace_tag_attrs(soup, u'form', [u'action'])
        self.replace_tag_attrs(soup, u'img', [u'src'])
        self.replace_tag_attrs(soup, u'meta', [u'content'])
        self.replace_tag_attrs(soup, u'span', [u'data-href'])
        self.replace_tag_attrs(soup, u'video', [u'src', u'poster'])
        self.replace_tag_attrs(soup, u'command', [u'icon'])
        self.replace_tag_attrs(soup, u'source', [u'src'])

        self.change_inline_style(soup)

        return soup.prettify()

    def replace_tag_attrs(self, soup, target_tag, target_attrs):
        for attr in target_attrs:
            for tag in soup.find_all(target_tag, **{attr: True}):
                try:
                    uri = tag[attr]
                except KeyError:
                    continue
                else:
                    access_uri = self.get_access_uri(uri)
                    tag[attr] = reverse(
                        u'viewer', args=(access_uri.get_cli_access_id(), )
                    )

        return soup

    def remove_tags(self, soup, target_tag):
        tags = soup.find_all(target_tag)
        for tag in tags:
            tag.extract()

        return soup

    def unwrap_tag(self, soup, target_tag):
        tags = soup.find_all(target_tag)
        for tag in tags:
            tag.unwrap()

        return soup

    def change_inline_style(self, soup):
        replacer = CSSReplacer(self.user, self.base_uri)

        for tag in soup.find_all(u'style'):
            tag.string = replacer.replace(tag.string)

        return soup


class CSSReplacer(URIReplacer):

    def replace(self, css):
        cssutils.log.setLevel(logging.CRITICAL)
        cssutils.cssproductions.MACROS[u'name'] = ur'[\*]?{nmchar}+'

        try:
            sheet = cssutils.parseString(css)
        except:
            sheet = cssutils.css.CSSStyleDeclaration(cssText=css)

        replacer = lambda url: reverse(
            u'viewer', args=(self.get_access_uri(url).get_cli_access_id(), )
        )
        cssutils.replaceUrls(sheet, replacer)

        return sheet.cssText


class ProxyModel(object):

    def __init__(self, request, access_uri, dns_list, cookies={}):
        self.request = request
        self.access_uri = access_uri
        self.dns_list = dns_list
        self.cookies = cookies
        self.request_uri = self.resolve_redirect(self.access_uri)

    def get_request_uri(self):
        return self.request_uri

    def get_ipaddr_based_uri(self, host_based_uri):
        parsed_uri = list(urlparse(host_based_uri))
        try:
            dns_cache = DNSCache.objects.get(fqdn=parsed_uri[1].lower())
        except DNSCache.DoesNotExist:
            dns_cache = DNSCache(fqdn=parsed_uri[1].lower())
            dns_cache.update_ip_addr(self.dns_list)
            dns_cache.save()
        else:
            if dns_cache.is_expired():
                dns_cache.update_ip_addr(self.dns_list)

        parsed_uri[1] = dns_cache.get_ip_addr()

        return urlunparse(parsed_uri)

    def resolve_redirect(self, request_uri, max_redirect_count=10):
        redirect_count = 0
        is_continue = True

        headers = {
            u'User-Agent': self.request.META.get(u'HTTP_USER_AGENT', u'')
        }

        while is_continue:
            if redirect_count > max_redirect_count:
                raise requests.TooManyRedirects

            parsed_uri = urlparse(request_uri)
            headers[u'Host'] = parsed_uri.hostname
            if parsed_uri.scheme == u'http':
                response = requests.head(
                    self.get_ipaddr_based_uri(request_uri),
                    headers=headers, cookies=self.cookies,
                    allow_redirects=False
                )
            else:
                response = requests.head(
                    request_uri,
                    headers=headers, cookies=self.cookies,
                    allow_redirects=False
                )

            if response.status_code in (301, 302):
                request_uri = response.headers[u'location']
                self.cookies.update(response.cookies)
                redirect_count += 1
            else:
                is_continue = False
        else:
            return request_uri

    def get_data(self):
        parsed_uri = urlparse(self.request_uri)
        headers = {
            u'User-Agent': self.request.META.get(u'HTTP_USER_AGENT', u''),
            u'Host': parsed_uri.hostname
        }

        if parsed_uri.scheme == u'http':
            response = requests.get(
                self.get_ipaddr_based_uri(self.request_uri),
                headers=headers, cookies=self.cookies, allow_redirects=False
            )
        else:
            response = requests.get(
                self.request_uri,
                headers=headers, cookies=self.cookies, allow_redirects=False,
                verify=True
            )

        self.cookies.update(response.cookies)

        return (
            response.status_code, response.headers.get(u'Content-Type', u''),
            response.content, response.encoding
        )
