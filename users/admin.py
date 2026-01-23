from django.contrib import admin
from .models import CustomUser, Branch, Holiday
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Branch)
admin.site.register(Holiday)