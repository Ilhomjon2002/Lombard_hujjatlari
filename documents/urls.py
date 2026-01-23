from django.urls import path
from . import views

# app_name = 'documents'

urlpatterns = [
    # Asosiy sahifalar
    path('branch/<int:branch_id>/',     views.branch_documents,     name='branch_documents'),
    path('create/',                     views.create_document,      name='create_order'),
    path('<int:order_id>/',             views.document_detail,      name='order_detail'),
    path('sign/<int:signature_id>/',    views.sign_document,        name='sign_order'),
    path('track/<int:order_id>/',       views.document_tracking,    name='order_tracking'),

    # AJAX/API endpointlar
    path('api/document-types/',         views.get_document_types,   name='api_document_types'),
    path('api/branch-employees/',       views.get_branch_employees, name='api_branch_employees'),

    # Qo‘shimcha imkoniyatlar (agar kerak bo‘lsa keyinchalik qo‘shiladi)
    # path('<int:order_id>/edit/',      views.edit_order,           name='edit_order'),
    # path('<int:order_id>/cancel/',    views.cancel_order,         name='cancel_order'),
]