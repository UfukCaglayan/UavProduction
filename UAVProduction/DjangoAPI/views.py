from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee,PartProduction,Part,Assembly, AssemblyPart,UavProduction
from django.contrib import messages
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import PartProductionForm, AssemblyForm, AssemblyPartForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import random
import string
from django.utils import timezone

def home(request):
    return render(request, 'home.html')

def partproduction(request):
    return render(request, 'partproduction/index.html')

def assembly(request):
    return render(request, 'assembly/index.html')

@csrf_protect  # CSRF koruması sağlıyor
def login(request):
    if request.method == 'POST':
        employee_sicil_no = request.POST.get('employee_sicil_no')
        password = request.POST.get('password')
        try:
            # Çalışanı Employee tablosunda ara
            employee = Employee.objects.get(employee_sicil_no=employee_sicil_no)

            # Şifre kontrolü
            if employee.password == password:  
                request.session['employee_id'] = employee.employee_id  # Oturum için ID saklama
                
                # Takım kontrolü: Montaj değilse partproduction, montajsa montaj sayfasına yönlendir
                if employee.team.team_id == 5:
                    return redirect('assembly')  # 'partproduction' URL'ine yönlendirme
                elif employee.team.team_id == 4:
                    return redirect('avionic')
                else:
                    return redirect('partproduction')  # 'assembly' URL'ine yönlendirme (Montaj sayfası)

            else:
                messages.error(request, 'Yanlış şifre')
        except Employee.DoesNotExist:
            messages.error(request, 'Çalışan bulunamadı.')

    return render(request, 'login.html')



def part_production_list(request):
    print("burada2")
    employee_id = request.session.get('employee_id')
    if not employee_id:
        # Eğer kullanıcı giriş yapmamışsa, login sayfasına yönlendir
        return redirect('login')

    try:
        # Employee modelinden ilgili çalışanı al
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        # Eğer kullanıcıya ait bir employee bulunamazsa
        messages.error(request, 'Çalışan bulunamadı.')
        return redirect('login')

    # DataTables parametrelerini al
    draw = request.GET.get('draw')
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Tüm verileri filtrele
    queryset = PartProduction.objects.filter(part__team=employee.team)
    if search_value:
        queryset = queryset.filter(
            Q(part__part_name__icontains=search_value) |
            Q(uav__uav_name__icontains=search_value)
        )

    # Toplam ve filtrelenmiş kayıt sayısı
    total_records = PartProduction.objects.count()
    filtered_records = queryset.count()

    # Sayfalama
    queryset = queryset[start:start+length]

    # JSON verisi oluştur
    data = []
    for part in queryset:
        data.append({
            'part_production_id': part.part_production_id,
            'part': part.part.part_name,  # Parça adı
            'uav': part.uav.uav_name if part.uav else 'Belirtilmedi',  # UAV adı
            'stock': f"{part.stock} adet",  # Stok bilgisi
            'production_type': part.get_production_type_display(),  # Üretim türü
            'production_time': part.production_time.strftime('%Y-%m-%d %H:%M'),  # Üretim zamanı
            'material_type': part.get_material_type_display(),  # Malzeme türü
            'dimensions': f"{part.length}x{part.width}x{part.height}",  # Boyutlar
            'weight': f"{part.weight} kg",  # Ağırlık
        })

    # JSON yanıtını döndür
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data,
    })

def create_partproduction(request):
    # Oturumdaki employee_id'yi al
    employee_id = request.session.get('employee_id')

    if not employee_id:
        # Eğer kullanıcı giriş yapmamışsa, login sayfasına yönlendir
        return redirect('login')

    try:
        # Employee modelinden ilgili çalışanı al
        employee = Employee.objects.get(employee_id=employee_id)

        # Kullanıcının ait olduğu takımı al
        team = employee.team

        # Formu oluştur
        if request.method == 'POST':
            form = PartProductionForm(employee, request.POST)
            if form.is_valid():
                try:
                    part_production = form.save(commit=False)

                    # Gizli part_id değerini alıyoruz ve part_production'a atıyoruz
                    part_id = form.cleaned_data['part_id']  # part_id'yi alıyoruz
                    part = Part.objects.get(part_id=part_id)  # part_id'yi kullanarak part'ı alıyoruz
                    part_production.part = part  # Part'ı PartProduction'a ekliyoruz
                    
                    # UAV'ya ait daha önce bir üretim kaydı var mı kontrol et
                    uav = part_production.uav
                    if PartProduction.objects.filter(uav=uav, part=part_production.part).exists():
                        messages.error(request, 'Bu UAV için daha önce bir parça üretimi yapılmış!')
                        return render(request, 'partproduction/create.html', {'form': form})

                    # Eğer daha önce bir üretim kaydı yoksa, yeni üretimi kaydet
                    part_production.save()
                    messages.success(request, 'Parça üretimi başarıyla yapıldı!')

                except Exception as e:
                    messages.error(request, f'Hata oluştu: {str(e)}')

        else:
            form = PartProductionForm(employee)

    except Employee.DoesNotExist:
        # Eğer kullanıcıya ait bir employee bulunamazsa
        messages.error(request, 'Çalışan bulunamadı.')
        return redirect('login')

    return render(request, 'partproduction/create.html', {'form': form})


def edit_partproduction(request, part_production_id):
    part_production = get_object_or_404(PartProduction, pk=part_production_id)

    # Oturumdaki çalışan bilgilerini al
    employee_id = request.session.get('employee_id')
    if not employee_id:
        # Eğer kullanıcı giriş yapmamışsa, login sayfasına yönlendir
        return redirect('login')

    # Employee modelinden ilgili çalışanı al
    employee = Employee.objects.get(employee_id=employee_id)  # Assuming the user has an associated employee

    # Formu başlat ve işle
    if request.method == 'POST':
        form = PartProductionForm(employee, request.POST, instance=part_production)
        if form.is_valid():
            existing_part_production = PartProduction.objects.get(pk=part_production_id)

            # Eski uav değerini kontrol et
            if existing_part_production.uav != form.cleaned_data['uav']:
                updated_uav = form.cleaned_data['uav']  # Formdan gelen yeni UAV
                # Yeni UAV için aynı parça üretimi var mı kontrol et
                if PartProduction.objects.filter(uav=updated_uav, part=part_production.part).exists():
                    messages.error(request, 'Bu UAV için bu parça zaten üretilmiş!')
                    return render(request, 'partproduction/edit.html', {
                        'form': form, 'part_production': part_production
                    })

            # Eğer kontrol geçerse, değişiklikleri kaydet
            form.save()
            messages.success(request, 'Parça üretimi başarıyla güncellendi.')
        else:
            messages.error(request, 'Formda hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = PartProductionForm(employee, instance=part_production)

    return render(request, 'partproduction/edit.html', {
        'form': form,
        'part_production': part_production
    })


@csrf_exempt
def delete_partproduction(request, part_production_id):
    if request.method == "POST":
        part_production = get_object_or_404(PartProduction, pk=part_production_id)
        print("silme " + part_production.part.part_name)
        part_production.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def assembly_list(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return redirect('login')

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Çalışan bulunamadı.')
        return redirect('login')

    draw = request.GET.get('draw')
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    queryset = AssemblyPart.objects.filter(assembly__uav__team=employee.team)
    if search_value:
        queryset = queryset.filter(
            Q(assembly__assembly_code__icontains=search_value) |
            Q(assembly__uav__uav_name__icontains=search_value) |
            Q(part__part_name__icontains=search_value)
        )

    total_records = AssemblyPart.objects.count()
    filtered_records = queryset.count()

    queryset = queryset[start:start + length]

    data = []
    for assembly_part in queryset:
        data.append({
            'assembly_part_id': assembly_part.assembly_part_id,
            'assembly_code': assembly_part.assembly.assembly_code,
            'uav_name': assembly_part.assembly.uav.uav_name,
            'part_name': assembly_part.part.part_name,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data,
    })

def create_assembly(request):
    if request.method == 'POST':
        # Montaj Başlangıcı
        if 'create_assembly' in request.POST:
            form = AssemblyForm(request.POST)
            if form.is_valid():
                # Montaj kaydını oluştur
                assembly = form.save(commit=False)
                # Montaj kodunu oluştur
                assembly.assembly_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                # Montaj kaydını veritabanına kaydet
                assembly.save()

                # Başarılı yanıt döndür
                return JsonResponse({
                    'success': True,
                    'assembly_code': assembly.assembly_code,
                    'assembly_id': assembly.assembly_id
                })
            else:
                # Eğer form geçerli değilse, form hatalarını döndür
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })

        # Parça Ekleme İşlemi
        elif 'add_part' in request.POST:
            part_form = AssemblyPartForm(request.POST)
            if part_form.is_valid():
                # Geçerli verileri al
                assembly = part_form.cleaned_data['assembly']
                part_production_id = request.POST.get('part_production')
                part_production = PartProduction.objects.get(part_production_id=part_production_id)
                # AssemblyPart modeline yeni kayıt ekle
                AssemblyPart.objects.create(assembly=assembly, part_production=part_production)

                # Başarı mesajı döndür
                return JsonResponse({'success': True})
            else:
                # Eğer form geçerli değilse, form hatalarını döndür
                return JsonResponse({
                    'success': False,
                    'errors': part_form.errors
                })

        # Üretim Tamamlama İşlemi
        elif 'complete_production' in request.POST:
            assembly_id = request.POST.get('assembly_id')
            try:
                # Montajı bul
                assembly = Assembly.objects.get(id=assembly_id)
                print("girdi")
                # Üretimi tamamla, yeni bir UavProduction kaydı oluştur
                uav_production = UavProduction.objects.create(
                    assembly=assembly,
                    production_time=timezone.now()  # Üretim zamanını şu an olarak ayarla
                )

                # Başarı mesajı döndür
                return JsonResponse({'success': True, 'uav_production_id': uav_production.id})
            except Assembly.DoesNotExist:
                return JsonResponse({'success': False, 'errors': 'Montaj bulunamadı'})
            
    # GET isteği için formu render et
    else:
        assembly_form = AssemblyForm()
        part_form = AssemblyPartForm()
        return render(request, 'assembly/create.html', {
            'assembly_form': assembly_form,
            'part_form': part_form
        })

    
def get_parts_for_assembly(request, assembly_id):
    try:
        # Seçilen montajın UAV'ını al
        assembly = Assembly.objects.get(assembly_id=assembly_id)
        uav = assembly.uav
        uav_name = uav.uav_name
        # UAV'ye göre partları filtrele
        partproductions = PartProduction.objects.filter(uav=uav)

        # Tüm parçaların listesini al (partlar tablosu üzerinden)
        all_parts = Part.objects.all()  # Tüm parçaları almak için Part tablosundan sorgu yapıyoruz.

        # Mevcut partproductionlar
        part_data = [{'part_id': partproduction.part_production_id, 'part_name': partproduction.part.part_name} 
                     for partproduction in partproductions]
        
        # Eksik parçaları bulalım
        missing_parts = []
        for part in all_parts:
            if not partproductions.filter(part=part).exists():
                missing_parts.append(part.part_name)
        # Eğer eksik parça yoksa, başarılı yanıtla parçaları döndür
        return JsonResponse({'success': True, 'parts': part_data,'missing_parts': missing_parts,'uav_name':uav_name})

    except Assembly.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Montaj kaydı bulunamadı', 'parts': []})