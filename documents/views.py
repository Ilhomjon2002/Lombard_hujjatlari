# documents/views.py (corrected and enhanced: Document ni Order ga birlashtirish, QR va signed_at o'zgartirish)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .models import OrderSignature, Notification, Order, OrderSigner
from users.models import CustomUser, Branch
from .forms import EditSignatureForm
import qrcode
from io import BytesIO
from django.core.files import File
import json
import os
import copy

# ReportLab imports for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Kirillcha shriftni ro'yxatdan o'tkazish
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
except Exception:
    # Font topilmasa tizim shriftlaridan foydalaniladi
    pass


@login_required
def branch_documents(request, branch_id):
    if request.user.role not in ['admin', 'director']:
        messages.error(request, "Ruxsat yo'q")
        return redirect('dashboard')

    branch = get_object_or_404(Branch, id=branch_id)

    selected_type = request.GET.get('type')

    orders = Order.objects.filter(branch=branch)

    # Tur bo‘yicha filter (I/CH, SH/T, buyruq)
    if selected_type in ['internal', 'external', 'official']:
        orders = orders.filter(document_type=selected_type)

    orders = orders.select_related(
        'branch',
        'created_by'
    ).prefetch_related(
        'signatures__user'
    )

    context = {
        'branch': branch,
        'documents': orders,
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
            
            # Frontenddan kelgan ma'lumotni to'g'ri o'qish (array yoki vergulli string)
            employee_ids_raw = request.POST.getlist('employees') or request.POST.getlist('employees[]')
            employee_ids = []
            for item in employee_ids_raw:
                if ',' in item:
                    employee_ids.extend([x.strip() for x in item.split(',') if x.strip()])
                else:
                    if item.strip():
                        employee_ids.append(item.strip())
                        
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
            return redirect('order_detail', order_id=order.id)

        except Exception as e:
            messages.error(request, f'Xatolik yuz berdi: {str(e)}')

    branches = Branch.objects.filter(parent_branch__isnull=True)
    employees = CustomUser.objects.values('id', 'first_name', 'last_name', 'role')  # Rol qo'shildi
    context = {
        'branches': branches,
        'employees': employees,
    }
    return render(request, 'documents/create_document.html', context)

@login_required
def document_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('branch', 'created_by')
                       .prefetch_related('signatures__user'),
        pk=order_id
    )

    can_view = (
        request.user.role == 'admin' or
        request.user.role == 'director' or
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
def document_tracking(request, order_id):
    if request.user.role not in ['admin', 'director']:
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')

    order = get_object_or_404(
        Order.objects.select_related('branch', 'created_by')
                       .prefetch_related('signatures__user'),
        pk=order_id
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
def edit_order(request, order_id):
    if request.user.role != 'admin':
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('dashboard')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        deadline_str = request.POST.get('deadline')

        order.title = title

        if deadline_str:
            try:
                order.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, "Muddati noto'g'ri formatda kiritildi, saqlanmadi")
        else:
            order.deadline = None

        order.save()
        messages.success(request, 'Hujjat muvaffaqiyatli yangilandi')
        return redirect('document_detail', document_id=order.id)

    context = {
        'order': order,
    }
    return render(request, 'documents/edit_order.html', context)

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
    return render(request, 'documents/edit_signature_time.html', context)


from qrcode.constants import ERROR_CORRECT_L
@login_required
@require_http_methods(["POST"])
def sign_with_fingerprint(request, signature_id):
    """Barmoq izi tasdiqlanganidan keyin hujjatni imzolash va QR kod yaratish"""
    signature = get_object_or_404(OrderSignature, id=signature_id, user=request.user)
    
    if signature.signed:
        return JsonResponse({'error': 'Bu hujjat allaqachon imzolangan'}, status=400)
    
    # Ketma-ket imzolash tekshiruvi
    if signature.order.signature_type == 'sequential':
        pending_previous = OrderSignature.objects.filter(
            order=signature.order,
            order_number__lt=signature.order_number,
            signed=False
        ).exists()
        
        if pending_previous:
            return JsonResponse({'error': 'Oldingi imzolar hali qo\'yilmagan'}, status=400)
    
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    
    comment = data.get('comment', '')
    custom_time_str = data.get('custom_time')
    
    if custom_time_str:
        try:
            # Datetime local format is usually 'YYYY-MM-DDTHH:MM'
            signed_at = datetime.strptime(custom_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            signed_at = datetime.now()
    else:
        signed_at = datetime.now()
    
    # QR kod ma'lumotlari
    user = request.user
    full_name = f"{user.last_name} {user.first_name} {user.middle_name}".strip()
    qr_data = (
        f"IMZO TASDIQLANGAN\n"
        f"F.I.O: {full_name}\n"
        f"Lavozim: {user.position or '-'}\n"
        f"Sarlavha: {signature.order.title}\n"
        f"Buyruq raqami: {signature.order.number}\n"
        f"Imzolangan: {signed_at.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"ID: {user.id}"
    )
    
    # QR kod generatsiya
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_L,
        box_size=4,
        border=2
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # QR kodni saqlash
    # qr_buffer = BytesIO()
    # qr_img.save(qr_buffer, format='PNG')
    # qr_buffer.seek(0)
    
    # Imzoni saqlash
    signature.signed = True
    signature.signed_at = signed_at
    signature.comment = comment
    
    # QR kodni ImageField ga saqlash
    qr_filename = f"qr_sign_{signature.order.number}_{user.username}_{signed_at.strftime('%Y%m%d%H%M%S')}.png"
    qr_save_buffer = BytesIO()
    qr_img.save(qr_save_buffer, format='PNG')
    qr_save_buffer.seek(0)
    signature.qr_code.save(qr_filename, File(qr_save_buffer), save=False)
    
    signature.save()
    
    # Word faylga alohida QR kod qo'shish bekor qilindi (PDF qatlamda qo'yiladi)
    word_embedded = False
    
    # Adminlarga xabar yuborish
    admins = CustomUser.objects.filter(role='admin')
    for admin in admins:
        Notification.objects.create(
            user=admin,
            notification_type='document_signed',
            order=signature.order,
            message=f"{user.get_full_name()} \"{signature.order.title}\" hujjatini barmoq izi bilan imzoladi"
        )
    
    # Javob
    response_data = {
        'success': True,
        'message': 'Hujjat muvaffaqiyatli imzolandi!',
        'word_updated': word_embedded,
    }
    
    if signature.qr_code:
        response_data['qr_code_url'] = signature.qr_code.url
    
    return JsonResponse(response_data)


@login_required
def download_pdf(request, order_id):
    """Buyruqni PDF shaklida yuklab olish — DOCX ham PDF ga konvertatsiya qilinadi"""
    import tempfile
    import os
    
    order = get_object_or_404(Order, id=order_id)
    
    # Ruxsat tekshirish
    can_view = (
        request.user.role == 'admin' or
        request.user.role == 'director' or
        request.user == order.created_by or
        order.signatures.filter(user=request.user).exists()
    )
    
    if not can_view:
        messages.error(request, "Ushbu hujjatni PDF variantini olishga ruxsat yo'q")
        return redirect('dashboard')
    
    if not order.file:
        messages.error(request, "Xatolik: Fayl topilmadi.")
        return redirect('order_detail', order_id=order.id)
    
    file_path = order.file.path
    if not os.path.exists(file_path):
        messages.error(request, "Xatolik: Fayl topilmadi.")
        return redirect('order_detail', order_id=order.id)
    
    temp_files = []
    pdf_path = None
    
    try:
        # === STEP 1: Get or create PDF ===
        if file_path.lower().endswith('.pdf'):
            pdf_path = file_path
        elif file_path.lower().endswith(('.doc', '.docx')):
            pdf_path = _convert_docx_to_pdf(file_path, temp_files)
        else:
            # Boshqa format - o'zini qaytaramiz
            with open(file_path, 'rb') as f:
                buffer = BytesIO(f.read())
            ext = os.path.splitext(file_path)[1]
            filename = f"hujjat_{order.number}{ext}".replace("/", "_")
            return FileResponse(buffer, as_attachment=True, filename=filename)
        
        if not pdf_path or not os.path.exists(pdf_path):
            messages.error(request, "PDF yaratishda xatolik yuz berdi.")
            return redirect('order_detail', order_id=order.id)
        
        # === STEP 2: Add QR codes overlay ===
        final_buffer = _add_qr_overlay(request, order, pdf_path, temp_files)
        
        filename = f"hujjat_{order.number}.pdf".replace("/", "_")
        return FileResponse(final_buffer, as_attachment=True, filename=filename)
        
    except Exception as e:
        print(f"download_pdf error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"PDF yaratishda xatolik: {e}")
        return redirect('order_detail', order_id=order.id)
    finally:
        # Vaqtinchalik fayllarni tozalash
        import shutil
        for tmp in temp_files:
            try:
                if os.path.isdir(tmp):
                    shutil.rmtree(tmp, ignore_errors=True)
                elif os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass


def _convert_docx_to_pdf(docx_path, temp_files):
    """DOCX faylni PDF ga konvertatsiya qilish — LibreOffice headless orqali (pixel-perfect)"""
    import tempfile
    import os
    import subprocess
    import shutil
    
    # LibreOffice yo'lini topish
    soffice_paths = [
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        '/usr/bin/soffice',
        '/usr/lib/libreoffice/program/soffice',
    ]
    
    soffice = None
    for path in soffice_paths:
        if os.path.exists(path):
            soffice = path
            break
    
    if not soffice:
        # PATH dan izlash
        soffice = shutil.which('soffice')
    
    if not soffice:
        raise FileNotFoundError("LibreOffice topilmadi. PDF konvertatsiya uchun LibreOffice o'rnatilishi kerak.")
    
    # Vaqtinchalik papka yaratish (LibreOffice output uchun)
    temp_dir = tempfile.mkdtemp()
    temp_files.append(temp_dir)  # tozalash uchun
    
    # DOCX faylni vaqtinchalik papkaga nusxalash (fayl nomi bilan ishlash uchun)
    docx_basename = os.path.basename(docx_path)
    temp_docx = os.path.join(temp_dir, docx_basename)
    shutil.copy2(docx_path, temp_docx)
    
    # LibreOffice headless mode bilan konvertatsiya
    try:
        result = subprocess.run(
            [
                soffice,
                '--headless',
                '--norestore',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                temp_docx
            ],
            capture_output=True,
            text=True,
            timeout=60,  # 60 soniya kutish
            cwd=temp_dir,
        )
        
        if result.returncode != 0:
            print(f"LibreOffice error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timed out after 60 seconds")
        raise
    except Exception as e:
        print(f"LibreOffice conversion error: {e}")
        raise
    
    # PDF fayl nomini aniqlash
    pdf_basename = os.path.splitext(docx_basename)[0] + '.pdf'
    output_pdf = os.path.join(temp_dir, pdf_basename)
    
    if not os.path.exists(output_pdf) or os.path.getsize(output_pdf) == 0:
        raise FileNotFoundError(f"LibreOffice PDF yaratmadi: {output_pdf}")
    
    # PDF ni doimiy temp faylga ko'chirish
    fd, final_pdf = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    temp_files.append(final_pdf)
    shutil.copy2(output_pdf, final_pdf)
    
    return final_pdf


def _add_qr_overlay(request, order, pdf_path, temp_files):
    """PDF ustiga QR kodlar qo'shish"""
    import tempfile
    import os
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    
    final_buffer = BytesIO()
    
    try:
        # QR-kod overlay yaratish
        overlay_buffer = BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        width, height = A4
        
        # --- Top Right: Hujjat QR (Download Link) ---
        download_url = request.build_absolute_uri(f"/documents/download-pdf/{order.id}/")
        qr = qrcode.QRCode(version=1, box_size=5, border=1)
        qr.add_data(download_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        fd, main_qr_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        temp_files.append(main_qr_path)
        img.save(main_qr_path, format='PNG')
        
        # Draw Main QR at Top Right
        qr_size = 60
        c.drawImage(main_qr_path, width - qr_size - 20, height - qr_size - 20, width=qr_size, height=qr_size)
        c.setFont("Helvetica", 8)
        c.drawString(width - qr_size - 30, height - qr_size - 30, f"Buyruq: {order.number}")
        
        # --- Bottom: Imzolar QR ---
        start_x = 40
        start_y = 40
        
        if order.director_approved and order.final_qr_code:
            try:
                qr_size_sig = 55
                c.drawImage(order.final_qr_code.path, start_x, start_y + 10, width=qr_size_sig, height=qr_size_sig)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(start_x, start_y, "Tasdiqlandi (Barcha imzolar)")
                if order.director_approved_at:
                    c.setFont("Helvetica", 6)
                    c.drawString(start_x, start_y - 8, order.director_approved_at.strftime("%d.%m.%Y %H:%M"))
            except Exception as e:
                print(f"Error drawing director final QR: {e}")
        else:
            signatures = order.signatures.filter(signed=True).order_by('order_number')
            if signatures.exists():
                qr_data_lines = [f"{order.title} ({order.number}) - Imzolaganlar:"]
                for index, sig in enumerate(signatures, 1):
                    time_str = sig.signed_at.strftime('%d.%m.%Y %H:%M') if sig.signed_at else '-'
                    pos = sig.user.position or 'Xodim'
                    qr_data_lines.append(f"{index}. {sig.user.get_full_name()} ({pos}) - {time_str}")
                
                sig_qr_data = "\n".join(qr_data_lines)
                
                sig_qr = qrcode.QRCode(version=1, box_size=5, border=1)
                sig_qr.add_data(sig_qr_data)
                sig_qr.make(fit=True)
                sig_img = sig_qr.make_image(fill='black', back_color='white')
                
                fd, sig_qr_path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                temp_files.append(sig_qr_path)
                sig_img.save(sig_qr_path, format='PNG')
                
                qr_size_sig = 50
                try:
                    c.drawImage(sig_qr_path, start_x, start_y + 10, width=qr_size_sig, height=qr_size_sig)
                    c.setFont("Helvetica-Bold", 7)
                    c.drawString(start_x, start_y, "Barcha imzolar QR kodi")
                    c.setFont("Helvetica", 6)
                    c.drawString(start_x, start_y - 8, f"{signatures.count()} ta xodim imzolagan")
                except Exception as e:
                    print(f"Error drawing consolidated sig QR: {e}")
        
        c.save()
        overlay_buffer.seek(0)
        
        # Asosiy PDF bilan overlay'ni birlashtirish
        overlay_pdf = PdfReader(overlay_buffer)
        overlay_page = overlay_pdf.pages[0]
        
        pdf_writer = PdfWriter()
        original_reader = PdfReader(pdf_path)
        
        for page_num in range(len(original_reader.pages)):
            page = original_reader.pages[page_num]
            if page_num == 0:
                # QR kodlarni faqat birinchi sahifaga qo'yish
                page.merge_page(overlay_page)
            pdf_writer.add_page(page)
        
        pdf_writer.write(final_buffer)
        
    except Exception as e:
        print(f"QR overlay error: {e}")
        import traceback
        traceback.print_exc()
        # Xato bo'lsa, original PDF ni qaytarish
        final_buffer = BytesIO()
        with open(pdf_path, 'rb') as f:
            final_buffer.write(f.read())
    
    final_buffer.seek(0)
    return final_buffer

@login_required
def director_approve_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user.role != 'director':
        messages.error(request, "Faqat direktor tasdiqlashi mumkin.")
        return redirect('dashboard')
    
    if not order.is_fully_signed():
        messages.error(request, "Barcha xodimlar imzolab bo'lmagan.")
        return redirect('order_detail', order_id=order.id)
        
    if order.director_approved:
        messages.info(request, "Bu hujjat allaqachon tasdiqlangan.")
        return redirect('order_detail', order_id=order.id)
        
    return render(request, 'documents/director_approve.html', {'order': order})

@require_http_methods(["POST"])
@login_required
def api_director_approve(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user.role != 'director':
        return JsonResponse({'error': "Ruxsat yo'q"}, status=403)
        
    if not order.is_fully_signed():
        return JsonResponse({'error': "Barcha xodimlar imzolamagan"}, status=400)
        
    if order.director_approved:
        return JsonResponse({'error': "Allaqachon tasdiqlangan"}, status=400)
        
    # Tasdiqlash
    order.director_approved = True
    order.director_approved_at = datetime.now()
    
    # Umumiy QR kod yaratish
    signatures = order.signatures.all().order_by('order_number')
    qr_data_lines = [f"Buyruq №: {order.number}"]
    qr_data_lines.append(f"Direktor: {request.user.get_full_name()} (Tasdiq: {order.director_approved_at.strftime('%d.%m.%Y %H:%M')})")
    qr_data_lines.append("--- Imzo chekkanlar ---")
    
    for sig in signatures:
        time_str = sig.signed_at.strftime('%d.%m.%Y %H:%M') if sig.signed_at else '-'
        pos = sig.user.position or 'Xodim'
        qr_data_lines.append(f"{sig.user.get_full_name()} ({pos}) - {time_str}")
        
    qr_data = "\n".join(qr_data_lines)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    order.final_qr_code.save(f"final_qr_{order.id}.png", File(buffer), save=False)
    order.save()
    
    Notification.objects.create(
        user=order.created_by,
        notification_type='status_changed',
        order=order,
        message=f"Sizning '{order.title}' buyrug'ingiz direktor tomonidan tasdiqlandi"
    )
    
    return JsonResponse({
        'success': True,
        'qr_code_url': order.final_qr_code.url if order.final_qr_code else ''
    })

