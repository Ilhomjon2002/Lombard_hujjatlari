from django.urls import path
from . import views

# app_name = 'users'

urlpatterns = [
    # Auth
    path('',          views.login_view,                 name='login'),
    path('logout/',         views.logout_view,          name='logout'),

    # Foydalanuvchi sahifalari
    path('dashboard/',      views.dashboard,            name='dashboard'),
    path('profile/',        views.profile,              name='profile'),
    path('notifications/',  views.notifications,        name='notifications'),

    # Admin / User management
    path('manage-users/',   views.manage_users,         name='manage_users'),
    path('branch-employees/<int:branch_id>/', views.branch_employees,     name='branch_employees'),
    path('create-user/',    views.create_user,          name='create_user'),
    path('edit-user/<int:user_id>/',    views.edit_user,            name='edit_user'),
    path('user/<int:user_id>/',         views.user_detail,          name='user_detail'),
    path('reset-password/<int:user_id>/', views.reset_user_password, name='reset_password'),
    path('toggle-status/<int:user_id>/',  views.toggle_user_status,   name='toggle_status'),

    # Qo‘shimcha (oldingi taklifda qo‘shilganlar, agar ishlatilsa)
    path('branches/create/',         views.create_branch,        name='create_branch'),
    # path('holidays/',                views.manage_holidays,      name='manage_holidays'),
    # path('holidays/create/',         views.create_holiday,       name='create_holiday'),
]