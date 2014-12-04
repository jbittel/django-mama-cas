# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ServiceTicket'
        db.create_table(u'mama_cas_serviceticket', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['profile.UserProfile'])),
            ('expires', self.gf('django.db.models.fields.DateTimeField')()),
            ('consumed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('primary', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'mama_cas', ['ServiceTicket'])

        # Adding model 'ProxyTicket'
        db.create_table(u'mama_cas_proxyticket', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['profile.UserProfile'])),
            ('expires', self.gf('django.db.models.fields.DateTimeField')()),
            ('consumed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('granted_by_pgt', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mama_cas.ProxyGrantingTicket'])),
        ))
        db.send_create_signal(u'mama_cas', ['ProxyTicket'])

        # Adding model 'ProxyGrantingTicket'
        db.create_table(u'mama_cas_proxygrantingticket', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ticket', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['profile.UserProfile'])),
            ('expires', self.gf('django.db.models.fields.DateTimeField')()),
            ('consumed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('iou', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('granted_by_st', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mama_cas.ServiceTicket'], null=True, on_delete=models.PROTECT, blank=True)),
            ('granted_by_pt', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mama_cas.ProxyTicket'], null=True, on_delete=models.PROTECT, blank=True)),
        ))
        db.send_create_signal(u'mama_cas', ['ProxyGrantingTicket'])


    def backwards(self, orm):
        # Deleting model 'ServiceTicket'
        db.delete_table(u'mama_cas_serviceticket')

        # Deleting model 'ProxyTicket'
        db.delete_table(u'mama_cas_proxyticket')

        # Deleting model 'ProxyGrantingTicket'
        db.delete_table(u'mama_cas_proxygrantingticket')


    models = {
        u'mama_cas.proxygrantingticket': {
            'Meta': {'object_name': 'ProxyGrantingTicket'},
            'consumed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {}),
            'granted_by_pt': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mama_cas.ProxyTicket']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'granted_by_st': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mama_cas.ServiceTicket']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iou': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'ticket': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['profile.UserProfile']"})
        },
        u'mama_cas.proxyticket': {
            'Meta': {'object_name': 'ProxyTicket'},
            'consumed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {}),
            'granted_by_pgt': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mama_cas.ProxyGrantingTicket']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ticket': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['profile.UserProfile']"})
        },
        u'mama_cas.serviceticket': {
            'Meta': {'object_name': 'ServiceTicket'},
            'consumed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'expires': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ticket': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['profile.UserProfile']"})
        },
        u'profile.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'auth_backend': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_number': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'ip_phone': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'manager': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['mama_cas']