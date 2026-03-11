from django.contrib import admin
from .models import CustomUser, Branch
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Branch)
