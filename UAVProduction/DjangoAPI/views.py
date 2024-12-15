from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee,PartProduction,Part,Assembly, AssemblyPart,UavProduction
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.http import JsonResponse
from .forms import PartProductionForm, AssemblyForm, AssemblyPartForm
from django.db.models import Q
import random
import string
from django.utils import timezone
from django.contrib.auth import logout

def home(request):
    return render(request, 'home.html')

def partproduction(request):
    return render(request, 'partproduction/index.html')

def assembly(request):
    return render(request, 'assembly/index.html')

@csrf_protect  # CSRF koruması sağlanıyor
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
                
                # Takım kontrolü: Çalışan hangi takımın içinde yer alıyorsa o sayfaya yönlendiriliyor
                if employee.team.team_id == 5:
                    return redirect('assembly')  
                elif employee.team.team_id == 4:
                    return redirect('avionic')
                else:
                    return redirect('partproduction')  

            else:
                messages.error(request, 'Yanlış şifre')
        except Employee.DoesNotExist:
            messages.error(request, 'Çalışan bulunamadı.')

    return render(request, 'login.html')



def part_production_list(request):
    employee_id = request.session.get('employee_id')
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
                    part_production = form.save(commit=False) #Her takım üyesinin sadece kendi takımına ait parçayı üretebilmesi için parçanın gösterilmesini ama enabledinin false olmasını sağlayacağız
                    part_id = form.cleaned_data['part_id']  # part_id'yi alıyoruz
                    part = Part.objects.get(part_id=part_id)  # part_id'yi kullanarak part'ı alıyoruz
                    part_production.part = part  # Part'ı PartProduction'a ekliyoruz
                    
                    # Aynı parça daha önce bu UAV için üretilmiş mi kontrol et
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
        messages.error(request, 'Çalışan bulunamadı.')
        return redirect('login')

    return render(request, 'partproduction/create.html', {'form': form})


def edit_partproduction(request, part_production_id):
    part_production = get_object_or_404(PartProduction, pk=part_production_id)

    employee_id = request.session.get('employee_id')
    if not employee_id:
        return redirect('login')

    employee = Employee.objects.get(employee_id=employee_id)  

    if request.method == 'POST':
        form = PartProductionForm(employee, request.POST, instance=part_production)
        if form.is_valid():
            existing_part_production = PartProduction.objects.get(pk=part_production_id) #Güncellenmeden önceki kanat bilgisine erişeceğiz. Eğer kanat değişmişse ve daha önce bu kanat eklendiyse hata verecek.

            if existing_part_production.uav != form.cleaned_data['uav']:
                updated_uav = form.cleaned_data['uav']  # Formdan gelen UAV
                # UAV için aynı parça üretimi var mı kontrol et
                if PartProduction.objects.filter(uav=updated_uav, part=part_production.part).exists():
                    messages.error(request, 'Bu UAV için bu parça zaten üretilmiş!')
                    return render(request, 'partproduction/edit.html', {
                        'form': form, 'part_production': part_production
                    })

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

                if part_production.stock_quantity > 0:
                    # Stoktan bir adet azalt
                    part_production.stock_quantity -= 1
                    part_production.save()   
                else:
                    return JsonResponse({
                    'success': False,
                    'message': 'Stokta yeterli parça bulunmamaktadır.'
                })

                #Üretilen Uav'a daha önce aynı parçadan monte edilmiş mi kontrol et 
                existing_part = AssemblyPart.objects.filter(assembly=assembly, part_production=part_production).first()
                if existing_part:
                    return JsonResponse({
                        'success': False,
                        'message': 'Bu parça zaten takılı.'
                    })
                    
                
                AssemblyPart.objects.create(assembly=assembly, part_production=part_production)
                
                # Üretilecek uçağa ne kadar parça eklendiğini bul
                mounted_parts_data = get_mounted_parts_data(assembly)

                return JsonResponse({'success': True, 'mounted_parts_data': mounted_parts_data})
            else:
                return JsonResponse({
                    'success': False,
                    'errors': part_form.errors
                })

        # Üretim Tamamlama İşlemi
        elif 'complete_production' in request.POST:
            part_form = AssemblyPartForm(request.POST)
            if part_form.is_valid():
                assembly = part_form.cleaned_data['assembly']

                # Montaj ile ilişkili parça sayısını al
                part_count = AssemblyPart.objects.filter(assembly=assembly).count()
                required_part_count = Part.objects.count()
                print(part_count, required_part_count)

                # Eksik parça kontrolü yap
                if part_count < required_part_count:
                    # Eksik parça var, hata döndür
                    return JsonResponse({
                        'success': False,
                        'error': f'Üretim tamamlanamıyor. {required_part_count - part_count} adet eksik parça mevcut.'
                    })

                # Eksik parça yoksa üretimi tamamla
                uav_production = UavProduction.objects.create(
                    assembly=assembly,
                    production_time=timezone.now(),  # Üretim zamanını şu an olarak ayarla
                    part_count=part_count  # Mevcut parça sayısını kaydet
                )

                return JsonResponse({'success': True, 'uav_production_id': uav_production.id})

    else:
        assembly_form = AssemblyForm()
        part_form = AssemblyPartForm()
        return render(request, 'assembly/create.html', {
            'assembly_form': assembly_form,
            'part_form': part_form
        })

def get_mounted_parts_data(assembly):
    #Belirli bir montaj için takılmış parçaların listesini döndür.
    mounted_parts = AssemblyPart.objects.filter(assembly=assembly)

    mounted_parts_data = [
        {
            'part_name': mounted_part.part_production.part.part_name
        }
        for mounted_part in mounted_parts
    ]
    return mounted_parts_data

    
def get_parts_for_assembly(request, assembly_id):
    try:
        # Seçilen montajın UAV'ını al
        assembly = Assembly.objects.get(assembly_id=assembly_id)
        uav = assembly.uav
        uav_name = uav.uav_name
        # UAV'ye göre üretilen parçaları filtrele
        partproductions = PartProduction.objects.filter(uav=uav)

        # Tüm parçaların listesini al 
        all_parts = Part.objects.all()  

        # Uav için üretilmiş parçalar
        part_data = [{'part_id': partproduction.part_production_id, 'part_name': partproduction.part.part_name} 
                     for partproduction in partproductions]
        
        # Eksik parçaların bulunması: Partproduction tablosunda ilgili uav için üretilmiş parçaları kontrol ediyoruz. Tüm parçalar içinde olupta partproduction içinde olmayan parçalar envanterdeki eksik parçalardır
        missing_parts = []
        for part in all_parts:
            if not partproductions.filter(part=part).exists():
                missing_parts.append(part.part_name)
        
        mounted_parts_data = get_mounted_parts_data(assembly)
        return JsonResponse({'success': True, 'parts': part_data,'missing_parts': missing_parts,'uav_name':uav_name,'mounted_parts_data':mounted_parts_data})

    except Assembly.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Montaj kaydı bulunamadı', 'parts': []})
    

def uav_production_list(request):
    search_value = request.GET.get('search[value]', '')
    
    draw = request.GET.get('draw')
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))

    productions = UavProduction.objects.all()

    if search_value:
        productions = productions.filter(
            Q(assembly__assembly_code__icontains=search_value) |
            Q(assembly__uav__uav_name__icontains=search_value)    
        )


    total_records = UavProduction.objects.count()  
    filtered_records = productions.count()  

    productions = productions[start:start + length]

    data = []
    for production in productions:
        assembly = production.assembly
        uav = assembly.uav
        data.append({
            'assembly_code': assembly.assembly_code,
            'uav_name': uav.uav_name,
            'part_count': production.part_count,
        })
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    })

def custom_logout(request):
    logout(request)  # Oturumdan çıkış yap
    return redirect('login')  # Giriş sayfasına yönlendir
