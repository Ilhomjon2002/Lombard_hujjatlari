from django.contrib import admin
from .models import *

admin.site.register(DocumentType)
admin.site.register(Order)
admin.site.register(OrderSigner)
admin.site.register(OrderSignature)
admin.site.register(Notification)
admin.site.register(AdditionalDocument)
admin.site.register(AdditionalDocumentTemplate)