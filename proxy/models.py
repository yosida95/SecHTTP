from random import choice
from string import ascii_letters, digits

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
    fqdn = models.CharField(max_length=200)
    ip_addr = models.IPAddressField()
    request_date = models.DateTimeField()

    def __unicode__(self):
        return self.fqdn
