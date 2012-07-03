from django.contrib import admin
from django import forms
from ios_notifications.models import Device, Notification, APNService
from django.conf.urls.defaults import patterns, url
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404


class APNServiceAdminForm(forms.ModelForm):
    class Meta:
        model = APNService

    START_CERT = '-----BEGIN CERTIFICATE-----'
    END_CERT = '-----END CERTIFICATE-----'
    START_KEY = '-----BEGIN RSA PRIVATE KEY-----'
    END_KEY = '-----END RSA PRIVATE KEY-----'

    def clean_certificate(self):
        if not self.START_CERT or not self.END_CERT in self.cleaned_data['certificate']:
            raise forms.ValidationError('Invalid certificate')
        return self.cleaned_data['certificate']

    def clean_private_key(self):
        if not self.START_KEY or not self.END_KEY in self.cleaned_data['private_key']:
            raise forms.ValidationError('Invalid private key')
        return self.cleaned_data['private_key']


class APNServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname')
    form = APNServiceAdminForm


class DeviceAdmin(admin.ModelAdmin):
    fields = ('token', 'is_active', 'service')
    list_display = ('token', 'is_active', 'service', 'last_notified_at', 'platform', 'display')


class NotificationAdmin(admin.ModelAdmin):
    exclude = ('last_sent_at',)
    list_display = ('message', 'badge', 'sound', 'created_at', 'last_sent_at')

    def get_urls(self):
        urls = super(NotificationAdmin, self).get_urls()
        notification_urls = patterns('',
            url(r'^(?P<id>\d+)/push-notification/$', self.admin_site.admin_view(self.admin_push_notification), name='admin_push_notification'),
        )
        return notification_urls + urls

    def admin_push_notification(self, request, **kwargs):
        notification = get_object_or_404(Notification, **kwargs)
        num_devices = 0
        if request.method == 'POST':
            service = notification.service
            num_devices = service.device_set.filter(is_active=True).count()
            notification.service.push_notification_to_devices(notification)
        return TemplateResponse(request, 'admin/ios_notifications/notification/push_notification.html',
                                {'notification': notification, 'num_devices': num_devices, 'sent': request.method == 'POST'},
                                current_app='ios_notifications')

admin.site.register(Device, DeviceAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(APNService, APNServiceAdmin)
