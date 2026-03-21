from django.urls import path
from . import views

# app_name = 'users'

urlpatterns = [
    # Auth
    path('',                                views.login_view,                   name='login'),
    path('logout/',                         views.logout_view,                  name='logout'),
    path('api/auth/fingerprint/register/complete',         views.fingerprint_register_complete_scanner, name='fingerprint_register_complete_scanner'),
    path('api/auth/fingerprint/authenticate',              views.fingerprint_authenticate_scanner, name='fingerprint_authenticate_scanner'),
    path('api/auth/fingerprint/auth/confirm',              views.fingerprint_auth_confirm,         name='fingerprint_auth_confirm'),
    path('api/auth/fingerprint/remove',                    views.fingerprint_remove_scanner,       name='fingerprint_remove_scanner'),
    path('api/auth/fingerprint/verify-signing',            views.fingerprint_verify_for_signing,   name='fingerprint_verify_for_signing'),
    
    # E-IMZO Authentication
    path('api/auth/eimzo/login',                           views.eimzo_login_api,                  name='eimzo_login'),

    path('api/auth/fingerprint/authenticate',              views.fingerprint_authenticate_scanner, name='fingerprint_authenticate_scanner'),
    path('api/auth/fingerprint/auth/confirm',              views.fingerprint_auth_confirm,         name='fingerprint_auth_confirm'),
    path('api/auth/fingerprint/remove',                    views.fingerprint_remove_scanner,       name='fingerprint_remove_scanner'),
    path('api/auth/fingerprint/verify-signing',            views.fingerprint_verify_for_signing,   name='fingerprint_verify_for_signing'),
    
    # User pages
    path('dashboard/',      views.dashboard,            name='dashboard'),
    path('profile/',        views.profile,              name='profile'),
    path('profile/scanner-register/', views.scanner_register, name='scanner_register'),
    path('notifications/',  views.notifications,        name='notifications'),

    # Admin / User management
    path('manage-users/',   views.manage_users,         name='manage_users'),
    path('branch-employees/<int:branch_id>/', views.branch_employees,     name='branch_employees'),
    path('create-user/',    views.create_user,          name='create_user'),
    path('edit-user/<int:user_id>/',    views.edit_user,            name='edit_user'),
    path('user/<int:user_id>/',         views.user_detail,          name='user_detail'),
    path('reset-password/<int:user_id>/', views.reset_user_password, name='reset_password'),
    path('toggle-status/<int:user_id>/',  views.toggle_user_status,   name='toggle_status'),

    # Additional
    path('branches/create/',         views.create_branch,        name='create_branch'),
    path('import-employees/',        views.import_employees_excel, name='import_employees'),
]
