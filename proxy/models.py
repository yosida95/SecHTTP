from django.db import models
from django.contrib.auth.models import User

class AccessURI(models.Model):
    user=models.ForeignKey(User)
    cli_access_id=models.CharField('number to access uri',max_length=10)
    create_date=models.DateTimeField('date created')
    proto=models.CharField('http or https',max_length=10)
    fqdn=models.CharField(max_length=200)
    path=models.CharField(max_length=300)

class DNSCache(models.Model):
    fqdn = models.CharField(max_length=200)
    ip_addr = models.IPAddressField()
    request_date = models.DateTimeField()
    def __unicode__(self):
        return self.fqdn


