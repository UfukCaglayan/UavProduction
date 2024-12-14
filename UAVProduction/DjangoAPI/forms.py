from django import forms
from django.utils import timezone
from .models import PartProduction, Uav, Part, Assembly,AssemblyPart
from django.forms.widgets import DateTimeInput


class PartProductionForm(forms.ModelForm):
    class Meta:
        model = PartProduction
        fields = [
            'uav', 
            'stock', 
            'production_type', 
            'production_time', 
            'material_type', 
            'length', 
            'width', 
            'height', 
            'weight'
        ]
        labels = {
            'uav': 'İHA Seçimi',
            'stock': 'Stok Durumu',
            'production_type': 'Üretim Tipi',
            'production_time': 'Üretim Zamanı',
            'material_type': 'Malzeme Tipi',
            'length': 'Uzunluk',
            'width': 'Genişlik',
            'height': 'Yükseklik',
            'weight': 'Ağırlık',
        }

    def __init__(self, employee, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Uav seçimi için uavları getiriyoruz.
        self.fields['uav'].queryset = Uav.objects.all()
        self.fields['uav'].empty_label = "Seçiniz"

        # Kullanıcının takımına ait parçayı alıyoruz
        part = Part.objects.filter(team=employee.team).first()

        

        # Gizli bir alan olarak part_id'yi ekliyoruz
        self.fields['part_id'] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=part.part_id,
            required=False
        )

        # Part adı sadece gösterilecek, zorunlu değil
        self.fields['part'] = forms.CharField(
            widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            initial=part.part_name,
            required=False
        )

        # 'production_time' alanını DateTimeInput ile değiştirdik
        self.fields['production_time'].widget = DateTimeInput(attrs={
            'type': 'datetime-local',  # DateTimeLocal input tipini kullanıyoruz
            'class': 'form-control',
        })

        # 'length', 'width', 'height' ve 'weight' alanlarına default değerler ekliyoruz
        self.fields['length'].initial = None
        self.fields['width'].initial = None
        self.fields['height'].initial = None
        self.fields['weight'].initial = None

        # Formdaki tüm inputlara form-control sınıfı ekliyoruz
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields = {k: self.fields[k] for k in [
        'part_id', 'part', 'uav', 'stock', 'production_type', 
        'production_time', 'material_type', 'length', 'width', 
        'height', 'weight'
        ]}

class AssemblyForm(forms.ModelForm):
    class Meta:
        model = Assembly
        fields = ['uav']
        widgets = {
            'uav': forms.Select(attrs={'class': 'form-control'})
        }
class AssemblyPartForm(forms.ModelForm):
    class Meta:
        model = AssemblyPart
        fields = ['assembly']  # 'part_production' alanını ekleyin
        widgets = {
            'assembly': forms.Select(attrs={'class': 'form-control select2', 'id': 'assembly-select'}),
        }
