# documents/views.py (corrected and enhanced: Document ni Order ga birlashtirish, QR va signed_at o'zgartirish)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from .models import DocumentType, OrderSignature, Notification, Order, OrderSigner
from users.models import CustomUser, Branch
from .forms import EditSignatureForm  # Yangi form qo'shish kerak (forms.py da)



@login_required
def branch_documents(request, branch_id):
    if request.user.role != 'admin':
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')

    branch = get_object_or_404(Branch, id=branch_id)
    document_types = DocumentType.objects.filter(branch=branch)

    # Hujjat turlari bo'yicha filter
    selected_type = request.GET.get('type')
    orders = Order.objects.filter(branch=branch)

    if selected_type:
        orders = orders.filter(document_type__name=selected_type)  # Agar Order da document_type bo'lsa qo'shish kerak edi, lekin yo'q, shuning uchun o'chirib tashlash yoki qo'shish

    orders = orders.select_related(
        'branch', 'created_by'
    ).prefetch_related('signatures__user')
    context = {
        'branch': branch,
        'document_types': document_types,
        'documents': orders,  # orders ga o'zgartirildi
        'selected_type': selected_type,
    }
    return render(request, 'documents/branch_documents.html', context)

@login_required
def create_document(request):
    if request.user.role != 'admin':
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            branch_id = request.POST.get('branch')
            # document_type_id = request.POST.get('document_type')  # Agar kerak bo'lsa qo'shish
            signature_type = request.POST.get('signature_type')
            employee_ids = request.POST.getlist('employees')
            file = request.FILES.get('file')
            deadline_str = request.POST.get('deadline')
            number = request.POST.get('number')

            branch = get_object_or_404(Branch, id=branch_id)
            # document_type = get_object_or_404(DocumentType, id=document_type_id)  # Agar kerak

            deadline = None
            if deadline_str:
                try:
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.warning(request, "Muddati noto'g'ri formatda kiritildi, saqlanmadi")

            order = Order.objects.create(
                title=title,
                branch=branch,
                # document_type=document_type,
                file=file,
                created_by=request.user,
                signature_type=signature_type,
                deadline=deadline,
                number=number
            )

            # Imzolar yaratish
            for i, emp_id in enumerate(employee_ids, start=1):
                try:
                    employee = CustomUser.objects.get(id=emp_id, role='employee')
                    OrderSigner.objects.create(
                        order=order,
                        user=employee,
                        order_number=i if signature_type == 'sequential' else 1,
                        required=True
                    )
                    OrderSignature.objects.create(
                        order=order,
                        user=employee,
                        order_number=i if signature_type == 'sequential' else 1,
                        signed=False
                    )

                    Notification.objects.create(
                        user=employee,
                        notification_type='signature_request',
                        order=order,
                        message=f"Sizdan \"{order.title}\" hujjatini imzolashingiz so'ralmoqda"
                    )
                except CustomUser.DoesNotExist:
                    continue

            messages.success(request, 'Hujjat muvaffaqiyatli yaratildi')
            return redirect('document_detail', document_id=order.id)

        except Exception as e:
            messages.error(request, f'Xatolik yuz berdi: {str(e)}')

    branches = Branch.objects.all()
    employees = CustomUser.objects.filter(role='employee').values('id', 'first_name', 'last_name', 'role')  # Rol qo'shildi
    context = {
        'branches': branches,
        'employees': employees,
    }
    return render(request, 'documents/create_document.html', context)

@login_required
def document_detail(request, document_id):
    order = get_object_or_404(
        Order.objects.select_related('branch', 'created_by')
                       .prefetch_related('signatures__user'),
        pk=document_id
    )

    can_view = (
        request.user.role == 'admin' or
        request.user == order.created_by or
        order.signatures.filter(user=request.user).exists()
    )

    if not can_view:
        messages.error(request, 'Ushbu hujjatni ko\'rishga ruxsat yo\'q')
        return redirect('dashboard')

    signatures = order.signatures.all()
    signature_status = [
        {
            'employee': sig.user.get_full_name(),
            'position': sig.order_number,
            'signed': sig.signed,
            'signed_at': sig.signed_at,
            'comment': sig.comment,
            'has_signature_image': bool(sig.signature_image),
            'has_qr_code': bool(sig.qr_code)
        }
        for sig in signatures
    ]

    context = {
        'document': order,
        'signatures': signatures,
        'signature_status': signature_status,
    }
    return render(request, 'documents/document_detail.html', context)

@login_required
def sign_document(request, signature_id):
    signature = get_object_or_404(OrderSignature, id=signature_id, user=request.user)

    if signature.signed:
        messages.warning(request, 'Siz bu hujjatni allaqachon imzolagansiz')
        return redirect('dashboard')

    # Ketma-ket imzolash tekshiruvi
    if signature.order.signature_type == 'sequential':
        pending_previous = OrderSignature.objects.filter(
            order=signature.order,
            order_number__lt=signature.order_number,
            signed=False
        ).exists()

        if pending_previous:
            messages.error(request, 'Oldingi imzolar hali qo‘yilmagan')
            return redirect('dashboard')

    if request.method == 'POST':
        if 'signature_image' in request.FILES:
            signature.signature_image = request.FILES['signature_image']

        signature.comment = request.POST.get('comment', '').strip()
        signature.signed = True
        signature.signed_at = datetime.now()
        signature.save()

        # Adminlarga xabar
        admins = CustomUser.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='document_signed',
                order=signature.order,
                message=f"{request.user.get_full_name()} \"{signature.order.title}\" hujjatini imzoladi"
            )

        messages.success(request, 'Hujjat muvaffaqiyatli imzolandi!')
        return redirect('dashboard')

    return render(request, 'documents/sign_document.html', {'signature': signature})

@login_required
def get_document_types(request):
    branch_id = request.GET.get('branch_id')
    if not branch_id:
        return JsonResponse({'document_types': []})

    types_qs = DocumentType.objects.filter(branch_id=branch_id)
    data = [{'id': t.id, 'name': t.name} for t in types_qs]

    return JsonResponse({'document_types': data})

@login_required
def get_branch_employees(request):
    branch_id = request.GET.get('branch_id')
    if not branch_id:
        return JsonResponse({'employees': []})

    employees = CustomUser.objects.filter(
        branch__id=branch_id,
        role='employee'
    ).distinct().values('id', 'first_name', 'last_name', 'username', 'role')  # Rol qo'shildi

    return JsonResponse({'employees': list(employees)})

@login_required
def document_tracking(request, document_id):
    if request.user.role != 'admin':
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')

    order = get_object_or_404(
        Order.objects.select_related('branch', 'created_by')
                       .prefetch_related('signatures__user'),
        pk=document_id
    )

    signatures = order.signatures.order_by('order_number')

    signature_history = [
        {
            'employee': sig.user.get_full_name(),
            'position': sig.order_number,
            'status': 'Imzolandi' if sig.signed else 'Kutilmoqda',
            'signed_at': sig.signed_at.strftime('%Y-%m-%d %H:%M') if sig.signed_at else None,
            'comment': sig.comment or '—',
        }
        for sig in signatures
    ]

    context = {
        'document': order,
        'signature_history': signature_history,
    }
    return render(request, 'documents/document_tracking.html', context)

@login_required
def edit_signature_time(request, signature_id):
    if request.user.role != 'admin':
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')
    
    signature = get_object_or_404(OrderSignature, id=signature_id)
    
    if request.method == 'POST':
        form = EditSignatureForm(request.POST, instance=signature)
        if form.is_valid():
            form.save()
            # QR kodni qayta generatsiya qilish
            signature.qr_code.delete(save=False)
            signature.save()  # save() ichida QR generatsiya qilinadi
            messages.success(request, 'Imzolangan vaqt o\'zgartirildi va QR kod yangilandi')
            return redirect('document_detail', document_id=signature.order.id)
    else:
        form = EditSignatureForm(instance=signature)
    
    context = {
        'form': form,
        'signature': signature,
    }
    return render(request, 'documents/edit_signature_time.html', context)  # Yangi template