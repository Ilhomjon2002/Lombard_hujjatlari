# users/views.py (corrected and enhanced)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import CustomUser, Branch, Holiday, FingerprintCredential
from documents.models import Notification, Order, OrderSigner, OrderSignature
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from .forms import CustomUserForm, UserUpdateForm, UserPasswordResetForm, UserProfileForm
from django.http import JsonResponse
from datetime import datetime
import json
import base64
import os
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


def login_view(request):
    """Handle user login with password or fingerprint"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has fingerprint registered
            has_fingerprint = hasattr(user, 'fingerprint_credential')
            
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name()}!')
            
            # Create notifications
            if user.role == 'employee':
                pending_signatures = OrderSignature.objects.filter(
                    user=user,
                    signed=False
                ).count()
                if pending_signatures > 0:
                    Notification.objects.create(
                        user=user,
                        notification_type='signature_request',
                        order=None,
                        message=f"You have {pending_signatures} documents waiting for signature"
                    )
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    
    # Notifications
    unread_notifications = Notification.objects.filter(
        user=user, 
        read=False
    ).count()
    
    if user.role == 'admin':
        # Admin dashboard
        branches = Branch.objects.all()
        recent_orders = Order.objects.all().order_by('-created_at')[:10]
        
        # User statistics
        total_users = CustomUser.objects.count()
        admin_count = CustomUser.objects.filter(role='admin').count()
        employee_count = CustomUser.objects.filter(role='employee').count()

        document_pending = Order.objects.filter(status='pending').count()
        document_signed = Order.objects.filter(status='completed').count()
        document_total = Order.objects.count()

        # Actual document lists for expandable panels
        all_orders = Order.objects.all().select_related('branch', 'created_by').order_by('-created_at')
        pending_orders = Order.objects.filter(status='pending').select_related('branch', 'created_by').order_by('-created_at')
        signed_orders = Order.objects.filter(status='completed').select_related('branch', 'created_by').order_by('-created_at')
        
        context = {
            'document_pending': document_pending,
            'document_signed': document_signed,
            'document_total': document_total,
            'branches': branches,
            'recent_orders': recent_orders,
            'unread_notifications': unread_notifications,
            'user_role': 'admin',
            'total_users': total_users,
            'admin_count': admin_count,
            'employee_count': employee_count,
            'all_orders': all_orders,
            'pending_orders': pending_orders,
            'signed_orders': signed_orders,
        }
        return render(request, 'users/admin_dashboard.html', context)
    
    elif user.role == 'director':
        # Director dashboard
        all_orders = Order.objects.all().select_related('branch', 'created_by').order_by('-created_at')
        
        pending_count = Order.objects.filter(status__in=['pending', 'partial']).count()
        completed_count = Order.objects.filter(status='completed').count()
        total_count = Order.objects.count()
        
        # Director o'zi imzolashi kerak bo'lgan hujjatlar
        my_pending = OrderSignature.objects.filter(
            user=user, signed=False,
            order__status__in=['pending', 'partial']
        ).select_related('order', 'order__branch').order_by('-order__created_at')
        
        my_signed = OrderSignature.objects.filter(
            user=user, signed=True
        ).select_related('order', 'order__branch').order_by('-signed_at')[:10]
        
        context = {
            'all_orders': all_orders,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'total_count': total_count,
            'my_pending': my_pending,
            'my_signed': my_signed,
            'unread_notifications': unread_notifications,
            'user_role': 'director',
        }
        return render(request, 'users/director_dashboard.html', context)
    
    else:
        # Employee dashboard
        pending_signatures = OrderSignature.objects.filter(
            user=user,
            signed=False,
            order__status__in=['pending', 'partial']
        ).select_related('order', 'order__branch').order_by('-order__created_at')
        
        signed_documents = OrderSignature.objects.filter(
            user=user,
            signed=True
        ).select_related('order', 'order__branch').order_by('-signed_at')[:10]
        
        notifications_list = Notification.objects.filter(
            user=user
        ).select_related('order').order_by('-created_at')[:10]
        
        context = {
            'pending_signatures': pending_signatures,
            'signed_documents': signed_documents,
            'notifications': notifications_list,
            'unread_notifications': unread_notifications,
            'user_role': 'employee',
        }
        return render(request, 'users/employee_dashboard.html', context)


@login_required
def profile(request):
    user = request.user
    has_fingerprint = hasattr(user, 'fingerprint_credential') and user.fingerprint_credential is not None
    
    if request.method == 'POST':
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
            user.save()
            messages.success(request, 'Profil rasmi muvaffaqiyatli yangilandi')
            return redirect('profile')
    
    context = {
        'user': user,
        'has_fingerprint': has_fingerprint,
    }
    return render(request, 'users/profile.html', context)


@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(read=False).count()
    
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(read=True)
        messages.success(request, 'All notifications marked as read')
        return redirect('notifications')
    
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def manage_users(request):
    if request.user.role != 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')

    # Filter parameters
    search_query = request.GET.get('search', '').strip()
    branch_filter_raw = request.GET.get('branch', '')
    try:
        branch_filter = int(branch_filter_raw) if branch_filter_raw else 0
    except (ValueError, TypeError):
        branch_filter = 0
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = CustomUser.objects.all()

    # Search
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Filter by branch (ManyToMany)
    if branch_filter:
        users = users.filter(branch__id=branch_filter).distinct()

    # Filter by role
    if role_filter:
        users = users.filter(role=role_filter)

    # Filter by status
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Pagination
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
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    branch = get_object_or_404(Branch, id=branch_id)
    employees = CustomUser.objects.filter(branch=branch).order_by('last_name', 'first_name')
    
    context = {
        'branch': branch,
        'employees': employees,
        'title': f"Employees in {branch.name}",
    }
    return render(request, 'users/branch_employees.html', context)


@login_required
def create_user(request):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, f"User {user.username} created successfully")
            return redirect('manage_users')
        else:
            messages.error(request, "Please fill in the form correctly")
    else:
        form = CustomUserForm()
    
    branches = Branch.objects.all()
    
    context = {
        'form': form,
        'branches': branches,
        'title': 'Add New User',
    }
    return render(request, 'users/create_user.html', context)


@login_required
def edit_user(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.username} information updated")
            return redirect('manage_users')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': 'Edit User',
    }
    return render(request, 'users/edit_user.html', context)


@login_required
def reset_user_password(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = UserPasswordResetForm(request.POST)
        if form.is_valid():
            user.password = make_password(form.cleaned_data['new_password1'])
            user.save()
            messages.success(request, f"Password for user {user.username} updated")
            return redirect('manage_users')
    else:
        form = UserPasswordResetForm()
    
    context = {
        'form': form,
        'user': user,
        'title': 'Reset Password',
    }
    return render(request, 'users/reset_password.html', context)


@login_required
def toggle_user_status(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, "You cannot change your own status")
        return redirect('manage_users')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} {status}")
    return redirect('manage_users')


@login_required
def user_detail(request, user_id):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # User statistics
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
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        
        branch = Branch.objects.create(
            name=name
        )
        messages.success(request, f"Branch {branch.name} created successfully")
        return redirect('dashboard')
    
    branches = Branch.objects.all()
    context = {
        'branches': branches,
        'title': 'Add New Branch',
    }
    return render(request, 'users/create_branch.html', context)


@login_required
def manage_holidays(request):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
        return redirect('dashboard')
    
    holidays = Holiday.objects.all()
    context = {
        'holidays': holidays,
    }
    return render(request, 'users/manage_holidays.html', context)


@login_required
def create_holiday(request):
    if not request.user.role == 'admin':
        messages.error(request, "You don't have access to this page")
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
            messages.success(request, "Holiday added successfully")
            return redirect('manage_holidays')
        except ValueError:
            messages.error(request, "Invalid date format")
    
    branches = Branch.objects.all()
    context = {
        'branches': branches,
    }
    return render(request, 'users/create_holiday.html', context)


# ============================================================================
# FINGERPRINT SCANNER AUTHENTICATION (USB ZKTeco)
# ============================================================================

from django.utils import timezone

# Agent endi frontend (JavaScript) orqali chaqiriladi
# Django server agent bilan to'g'ridan-to'g'ri bog'lanmaydi
AGENT_URL = 'http://127.0.0.1:8001'  # Faqat frontend JS uchun ma'lumot


@require_http_methods(["GET"])
def scanner_status(request):
    """Scanner status — frontend JS agent'ni to'g'ridan-to'g'ri tekshiradi.
    Bu endpoint faqat fallback sifatida."""
    return JsonResponse({
        'agent_url': AGENT_URL,
        'message': 'Agent statusini JS orqali tekshiring'
    })


@login_required
def scanner_register_page(request):
    """Render the scanner fingerprint registration page"""
    return render(request, 'users/scanner_register.html', {
        'agent_url': AGENT_URL
    })


@login_required
@require_http_methods(["POST"])
def fingerprint_register_start_scanner(request):
    """Start fingerprint registration process — agent JS orqali tekshiriladi"""
    return JsonResponse({
        'status': 'ready',
        'agent_url': AGENT_URL,
        'message': "Barmog'ingizni skanerga qo'ying"
    })


@login_required
@require_http_methods(["GET"])
def fingerprint_capture(request):
    """Capture endpoint — frontend JS agent'dan to'g'ridan-to'g'ri oladi.
    Bu endpoint faqat fallback/info."""
    return JsonResponse({
        'agent_url': AGENT_URL,
        'capture_endpoint': f'{AGENT_URL}/api/fingerprint/capture',
        'message': 'JS orqali agent capture endpointiga murojaat qiling'
    })


@login_required
@require_http_methods(["POST"])
def fingerprint_register_complete_scanner(request):
    """Complete fingerprint registration — JS agent'dan template oladi va shu yerga yuboradi"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        template_b64 = data.get('template')
        quality = data.get('quality', 0)
        finger_position = data.get('finger_position', 'right_index')
        
        if not template_b64:
            return JsonResponse({
                'error': 'Barmoq izi shabloni yuborilmadi'
            }, status=400)
        
        # Decode base64 template and save to DB
        template_bytes = base64.b64decode(template_b64)
        
        from .models import ScannerFingerprintTemplate
        template_obj, created = ScannerFingerprintTemplate.objects.get_or_create(
            user=user,
            defaults={
                'template_data': template_bytes,
                'quality_score': quality,
                'finger_position': finger_position,
                'is_registered': True,
                'algorithm': 'ZKTECO_MINEX',
            }
        )
        
        if not created:
            template_obj.template_data = template_bytes
            template_obj.quality_score = quality
            template_obj.finger_position = finger_position
            template_obj.is_registered = True
            template_obj.algorithm = 'ZKTECO_MINEX'
            template_obj.save()
        
        # Enable fingerprint on user
        user.fingerprint_enabled = True
        user.save()
        
        return JsonResponse({
            'message': "Barmoq izi muvaffaqiyatli ro'yxatdan o'tkazildi",
            'redirect': '/profile/',
            'status': 'success'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': "So'rov formati noto'g'ri"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Xatolik: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def fingerprint_authenticate_scanner(request):
    """Fingerprint authentication for login.
    
    Flow:
    1. JS bu endpoint'ga username yuboradi
    2. Django stored_template qaytaradi
    3. JS agent'da capture + verify qiladi
    4. JS natijani /fingerprint/auth/confirm/ ga yuboradi
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({
                'error': 'Foydalanuvchi nomi kerak'
            }, status=400)
        
        # Check user exists and has fingerprint
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'error': 'Foydalanuvchi topilmadi'
            }, status=404)
        
        if not user.fingerprint_enabled:
            return JsonResponse({
                'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
            }, status=400)
        
        try:
            fp_template = user.scanner_fingerprint
            if not fp_template.is_registered:
                return JsonResponse({
                    'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
                }, status=400)
        except:
            return JsonResponse({
                'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
            }, status=400)
        
        # Return stored template for JS verification via agent
        stored_template_b64 = base64.b64encode(bytes(fp_template.template_data)).decode()
        
        return JsonResponse({
            'status': 'ready',
            'stored_template': stored_template_b64,
            'agent_url': AGENT_URL,
            'message': "Barmog'ingizni skanerga qo'ying"
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': "So'rov formati noto'g'ri"
        }, status=400)


@require_http_methods(["POST"])
def fingerprint_auth_confirm(request):
    """Confirm fingerprint authentication after JS verified via agent.
    
    JS agent'da verify qilgandan keyin natijani shu yerga yuboradi.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        match = data.get('match', False)
        score = data.get('score', 0)
        
        if not username or not match:
            return JsonResponse({
                'error': 'Barmoq izi mos kelmadi'
            }, status=401)
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'error': 'Foydalanuvchi topilmadi'
            }, status=404)
        
        # Verify the user has fingerprint enabled
        if not user.fingerprint_enabled:
            return JsonResponse({
                'error': 'Barmoq izi faol emas'
            }, status=400)
        
        # Log user in
        login(request, user)
        
        # Update verification stats
        try:
            fp_template = user.scanner_fingerprint
            fp_template.last_verified = timezone.now()
            fp_template.verification_count = (fp_template.verification_count or 0) + 1
            fp_template.save()
        except:
            pass
        
        return JsonResponse({
            'status': 'success',
            'message': "Muvaffaqiyatli kirdingiz!",
            'redirect': '/dashboard/'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': "So'rov formati noto'g'ri"
        }, status=400)


@login_required
@require_http_methods(["POST"])
def fingerprint_verify_for_signing(request):
    """Verify fingerprint before document signing.
    
    Flow:
    1. JS bu endpoint'ga so'rov yuboradi (action='get_template')
    2. Django stored_template qaytaradi
    3. JS agent'da capture + verify qiladi
    4. JS natijani shu endpoint'ga qaytaradi (action='confirm')
    """
    user = request.user
    
    if not user.fingerprint_enabled:
        return JsonResponse({
            'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
        }, status=400)
    
    try:
        fp_template = user.scanner_fingerprint
        if not fp_template.is_registered:
            return JsonResponse({
                'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
            }, status=400)
    except:
        return JsonResponse({
            'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
        }, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action', 'get_template')
        
        if action == 'get_template':
            # Step 1: Return stored template for JS to verify via agent
            stored_template_b64 = base64.b64encode(bytes(fp_template.template_data)).decode()
            return JsonResponse({
                'status': 'ready',
                'stored_template': stored_template_b64,
                'agent_url': AGENT_URL,
                'message': "Barmog'ingizni skanerga qo'ying"
            })
        
        elif action == 'confirm':
            # Step 2: JS verified via agent, confirm the result
            match = data.get('match', False)
            score = data.get('score', 0)
            
            if not match:
                return JsonResponse({
                    'verified': False,
                    'error': 'Barmoq izi mos kelmadi'
                }, status=401)
            
            fp_template.last_verified = timezone.now()
            fp_template.verification_count = (fp_template.verification_count or 0) + 1
            fp_template.save()
            
            return JsonResponse({
                'verified': True,
                'message': 'Barmoq izi tasdiqlandi'
            })
        
        else:
            return JsonResponse({
                'error': "Noto'g'ri amal"
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': "So'rov formati noto'g'ri"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Xatolik: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def fingerprint_remove_scanner(request):
    """Remove registered fingerprint"""
    user = request.user
    
    try:
        fp_template = user.scanner_fingerprint
    except:
        return JsonResponse({
            'error': "Barmoq izi ro'yxatdan o'tkazilmagan"
        }, status=404)
    
    try:
        fp_template.delete()
        user.fingerprint_enabled = False
        user.save()
        
        return JsonResponse({
            'message': "Barmoq izi muvaffaqiyatli o'chirildi",
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Xatolik: {str(e)}'
        }, status=500)


# fingerprint_verify_scanner endi fingerprint_auth_confirm va
# fingerprint_verify_for_signing ichiga birlashtirildi (yuqorida)


@login_required
def import_employees_excel(request):
    """Excel fayldan ishchilarni import qilish"""
    if request.user.role != 'admin':
        messages.error(request, "Ruxsat yo'q")
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Faqat Excel (.xlsx, .xls) fayllar qabul qilinadi")
            return redirect('import_employees')
        
        try:
            import openpyxl
            
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            # Transliteratsiya funksiyasi (kirill → lotin)
            cyrillic_to_latin = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
                'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
                'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
                'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
                'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
                'э': 'e', 'ю': 'yu', 'я': 'ya',
            }
            
            def transliterate(text):
                result = ''
                for char in text.lower():
                    result += cyrillic_to_latin.get(char, char)
                return result
            
            def make_username(fio):
                """FIO dan username yaratish: familiya.ism formatida"""
                parts = fio.strip().split()
                if len(parts) >= 2:
                    # Familiya + Ism
                    surname = transliterate(parts[0])
                    name = transliterate(parts[1])
                    username = f"{surname}.{name}"
                elif len(parts) == 1:
                    username = transliterate(parts[0])
                else:
                    return None
                
                # Faqat harflar va nuqta
                username = ''.join(c for c in username if c.isalnum() or c == '.')
                return username.lower()
            
            created_users = []
            skipped_users = []
            errors = []
            
            # Sarlavha qatorini o'tkazib yuborish (1-qator)
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            
            for i, row in enumerate(rows, start=2):
                if not row or not any(row):
                    continue
                
                # Ustunlarni o'qish
                org_name = str(row[0]).strip() if row[0] else ''
                fio = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                position = str(row[2]).strip() if len(row) > 2 and row[2] else ''
                
                if not fio:
                    errors.append(f"Qator {i}: FIO bo'sh")
                    continue
                
                # Username yaratish
                username = make_username(fio)
                if not username:
                    errors.append(f"Qator {i}: '{fio}' dan username yaratib bo'lmadi")
                    continue
                
                # Username takrorlanmasligini tekshirish
                original_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                # FIO ni ajratish
                name_parts = fio.split()
                last_name = name_parts[0] if len(name_parts) >= 1 else ''
                first_name = name_parts[1] if len(name_parts) >= 2 else ''
                
                # User yaratish
                user = CustomUser.objects.create_user(
                    username=username,
                    password='Ab123456',
                    first_name=first_name,
                    last_name=last_name,
                    role='employee',
                )
                
                # Filial/tashkilotni topish va bog'lash
                if org_name:
                    branch, _ = Branch.objects.get_or_create(
                        name=org_name,
                        defaults={'parent_branch': None}
                    )
                    user.branch.add(branch)
                
                created_users.append({
                    'fio': fio,
                    'username': username,
                    'password': 'Ab123456',
                    'org': org_name,
                    'position': position,
                })
            
            if created_users:
                messages.success(request, f"{len(created_users)} ta ishchi muvaffaqiyatli qo'shildi!")
            if skipped_users:
                messages.warning(request, f"{len(skipped_users)} ta ishchi o'tkazib yuborildi")
            if errors:
                messages.warning(request, f"Xatoliklar: {'; '.join(errors[:5])}")
            
            return render(request, 'users/import_result.html', {
                'created_users': created_users,
                'skipped_users': skipped_users,
                'errors': errors,
            })
            
        except Exception as e:
            messages.error(request, f"Excel faylni o'qishda xatolik: {str(e)}")
            return redirect('import_employees')
    
    return render(request, 'users/import_employees.html')



    