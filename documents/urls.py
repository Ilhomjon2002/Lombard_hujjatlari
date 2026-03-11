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
    path('approve/<int:order_id>/',     views.director_approve_page,name='director_approve_order'),
    path('download-pdf/<int:order_id>/', views.download_pdf,         name='download_pdf'),
    path('download-docx/<int:order_id>/', views.download_docx,       name='download_docx'),
    path('verify/<int:order_id>/',       views.verify_document,      name='verify_document'),
    path('upload-stamped/<int:order_id>/', views.upload_stamped_pdf, name='upload_stamped_pdf'),
    path('download-stamped/<int:order_id>/', views.download_stamped_pdf, name='download_stamped_pdf'),
    path('download-additional-doc/<int:doc_id>/', views.download_additional_document, name='download_additional_doc'),
    path('upload-additional-doc/<int:doc_id>/<int:order_id>/', views.upload_additional_document_file, name='upload_additional_document_file'),
    path('add-new-additional-doc/<int:order_id>/', views.add_new_additional_document, name='add_new_additional_document'),

    path('rename-additional-doc/<int:doc_id>/', views.rename_additional_document, name='rename_additional_document'),
    path('rename-additional-doc-template/<int:template_id>/', views.rename_additional_document_template, name='rename_additional_document_template'),

    # AJAX/API endpointlar
    path('api/branch-employees/',       views.get_branch_employees, name='api_branch_employees'),
    path('api/sign-fingerprint/<int:signature_id>/', views.sign_with_fingerprint, name='sign_with_fingerprint'),
    path('api/sign-additional-doc-fingerprint/<int:doc_id>/', views.sign_additional_doc_fingerprint, name='sign_additional_doc_fingerprint'),
    path('api/approve-fingerprint/<int:order_id>/',  views.api_director_approve,  name='api_director_approve'),

    # Qo‘shimcha imkoniyatlar (agar kerak bo‘lsa keyinchalik qo‘shiladi)
    path('<int:order_id>/edit/',      views.edit_order,           name='order_update'),
    path('<int:order_id>/delete/',    views.delete_order,         name='delete_order'),
]