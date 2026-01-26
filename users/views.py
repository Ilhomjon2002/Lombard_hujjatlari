# users/views.py (corrected and enhanced)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import CustomUser, Branch, Holiday
from documents.models import Notification, Order, OrderSigner, OrderSignature
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from .forms import CustomUserForm, UserUpdateForm, UserPasswordResetForm, UserProfileForm
from django.http import JsonResponse


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Xush kelibsiz, {user.get_full_name()}!')
            
            # Bildirishnomalarni yaratish
            if user.role == 'employee':
                pending_signatures = OrderSignature.objects.filter(
                    user=user,
                    signed=False
                ).count()
                if pending_signatures > 0:
                    Notification.objects.create(
                        user=user,
                        notification_type='signature_request',
                        document=None,
                        message=f"Sizda {pending_signatures} ta imzolash kerak bo'lgan buyruq mavjud"
                    )
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Login yoki parol noto\'g\'ri')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Tizimdan chiqdingiz')
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
    
    # Bildirishnomalar
    unread_notifications = Notification.objects.filter(
        user=user, 
        read=False
    ).count()
    
    if user.role=='admin':
        # Admin uchun dashboard
        branches = Branch.objects.all()
        recent_orders = Order.objects.all().order_by('-created_at')[:10]
        
        # User statistics
        total_users = CustomUser.objects.count()
        admin_count = CustomUser.objects.filter(role='admin').count()
        employee_count = CustomUser.objects.filter(role='employee').count()

        document_pending = Order.objects.filter(status='pending').count()
        document_signed = Order.objects.filter(status='signed').count()
        document_total = Order.objects.count()

        main_branches = Branch.objects.filter(parent_branch__isnull=True)
        
        context = {
            'document_pending': document_pending,
            'document_signed' : document_signed,
            'document_total'  : document_total,
            'branches': branches,
            'recent_orders': recent_orders,
            'unread_notifications': unread_notifications,
            'user_role': 'admin',
            'total_users': total_users,
            'admin_count': admin_count,
            'employee_count': employee_count,
        }
        return render(request, 'users/admin_dashboard.html', context)
    
    else:
        # Ishchi uchun dashboard
        pending_signatures = Order.objects.filter(
            signers__user=user,
            status__in=['pending', 'partial']
        ).distinct()
        
        my_orders = Order.objects.filter(
            created_by=user
        ).order_by('-created_at')[:5]
        
        context = {
            'pending_signatures': pending_signatures,
            'my_orders': my_orders,
            'unread_notifications': unread_notifications,
            'user_role': 'employee',
        }
        return render(request, 'users/employee_dashboard.html', context)

@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        if 'signature_image' in request.FILES:
            user.signature_image = request.FILES['signature_image']
            user.save()
            messages.success(request, 'Imzo rasmi muvaffaqiyatli yangilandi')
            return redirect('profile')
    
    return render(request, 'users/profile.html', {'user': user})

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(read=False).count()
    
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(read=True)
        messages.success(request, 'Barcha bildirishnomalar o\'qilgan deb belgilandi')
        return redirect('notifications')
    
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def manage_users(request):
    if request.user.role != 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')

    # Filter parametrlari
    search_query = request.GET.get('search', '').strip()
    branch_filter = request.GET.get('branch', '')
    role_filter   = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = CustomUser.objects.all()

    # Qidiruv
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Filial bo'yicha filter (ManyToMany uchun to'g'ri yozilishi)
    if branch_filter:
        users = users.filter(branch__id=branch_filter).distinct()

    # Rol bo'yicha
    if role_filter:
        users = users.filter(role=role_filter)

    # Status bo'yicha
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Sahifalash
    paginator = Paginator(users.order_by('-date_joined'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    branches = Branch.objects.all()

    context = {
        'users': page_obj,
        'branches': branches,
        'search_query': search_query,
        'branch_filter': branch_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'page_obj': page_obj,
    }
    return render(request, 'users/manage_users.html', context)



@login_required
def branch_employees(request, branch_id):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    employees = CustomUser.objects.filter(branch=branch).order_by('last_name', 'first_name')
    
    context = {
        'branch': branch,
        'employees': employees,
        'title': f"{branch.name} filialidagi xodimlar",
    }
    return render(request, 'users/branch_employees.html', context)


@login_required
def create_user(request):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, f"Foydalanuvchi {user.username} muvaffaqiyatli yaratildi")
            return redirect('manage_users')
        else:
            messages.error(request, "Iltimos, formani to'g'ri to'ldiring")
    else:
        form = CustomUserForm()
    
    branches = Branch.objects.all()
    
    context = {
        'form': form,
        'branches': branches,
        'title': 'Yangi foydalanuvchi qo\'shish',
    }
    return render(request, 'users/create_user.html', context)

@login_required
def edit_user(request, user_id):
    if not request.user.role=='admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Foydalanuvchi {user.username} ma'lumotlari yangilandi")
            return redirect('manage_users')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': 'Foydalanuvchini tahrirlash',
    }
    return render(request, 'users/edit_user.html', context)

@login_required
def reset_user_password(request, user_id):
    if not request.user.role=='admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserPasswordResetForm(request.POST)
        if form.is_valid():
            user.password = make_password(form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, f"Foydalanuvchi {user.username} paroli yangilandi")
            return redirect('manage_users')
    else:
        form = UserPasswordResetForm()
    
    context = {
        'form': form,
        'user': user,
        'title': 'Parolni yangilash',
    }
    return render(request, 'users/reset_password.html', context)

@login_required
def toggle_user_status(request, user_id):
    if not request.user.role=='admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, "O'zingizni faolligini o'zgartira olmaysiz")
        return redirect('manage_users')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "faollashtirildi" if user.is_active else "faolsizlashtirildi"
    messages.success(request, f"Foydalanuvchi {user.username} {status}")
    return redirect('manage_users')

@login_required
def user_detail(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Foydalanuvchi statistikasi
    created_orders = Order.objects.filter(created_by=user).count()
    pending_signatures = Order.objects.filter(
        signers__user=user,
        status__in=['pending', 'partial']
    ).count()
    completed_signatures = OrderSignature.objects.filter(
        user=user,
        signed=True
    ).count()
    context = {
        'user': user,
        'created_orders': created_orders,
        'pending_signatures': pending_signatures,
        'completed_signatures': completed_signatures,
    }
    return render(request, 'users/user_detail.html', context)

@login_required
def create_branch(request):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent_branch')
        
        parent = None
        if parent_id:
            parent = get_object_or_404(Branch, id=parent_id)
        
        branch = Branch.objects.create(
            name=name,
            parent_branch=parent
        )
        messages.success(request, f"Filial {branch.name} muvaffaqiyatli yaratildi")
        return redirect('dashboard')  # Yangi view qo'shish kerak bo'lsa
    
    branches = Branch.objects.all()
    main_branches = Branch.objects.filter(parent_branch__isnull=True)
    context = {
        'main_branches': main_branches,
        'branches': branches,
        'title': 'Yangi filial qo\'shish',
    }
    return render(request, 'users/create_branch.html', context)  # Yangi template kerak

@login_required
def manage_holidays(request):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    holidays = Holiday.objects.all()
    context = {
        'holidays': holidays,
    }
    return render(request, 'users/manage_holidays.html', context)  # Yangi template

@login_required
def create_holiday(request):
    if not request.user.role == 'admin':
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q")
        return redirect('dashboard')
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        description = request.POST.get('description')
        branch_id = request.POST.get('branch')
        
        branch = None
        if branch_id:
            branch = get_object_or_404(Branch, id=branch_id)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            Holiday.objects.create(date=date, description=description, branch=branch)
            messages.success(request, "Dam olish kuni qo'shildi")
            return redirect('manage_holidays')
        except ValueError:
            messages.error(request, "Sana formati noto'g'ri")
    
    branches = Branch.objects.all()
    context = {
        'branches': branches,
    }
    return render(request, 'users/create_holiday.html', context)  # Yangi template