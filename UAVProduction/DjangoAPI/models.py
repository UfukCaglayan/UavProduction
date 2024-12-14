from django.db import models
import random
import string
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=50)

    def __str__(self):
        return self.team_name

class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=50)
    employee_sicil_no = models.CharField(max_length=20, blank=True, unique=True, editable=False)
    password = models.CharField(max_length=255, blank=True, editable=False)
    last_login = models.DateTimeField(blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        # Sicil numarasını otomatik oluştur
        if not self.employee_sicil_no:
            self.employee_sicil_no = self.generate_sicil_no()
        
        # Şifreyi hash'lemiyoruz, düz metin olarak saklıyoruz
        if self.password and len(self.password) < 255:  # Şifreyi hash'lememek için kontrol
            pass  # Şifreyi olduğu gibi bırakıyoruz

        super().save(*args, **kwargs)

    def generate_sicil_no(self):
        """ Sicil numarasını sadece rakamlardan oluşturur. """
        return ''.join(random.choices(string.digits, k=8))

    def generate_random_password(self):
        """ 8 haneli rastgele bir parola oluşturur. """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    def check_password(self, raw_password):
        """ Şifreyi düz metin olarak kontrol etmek için kullanılan fonksiyon """
        return raw_password == self.password
    
class Part(models.Model):
    part_id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    part_name = models.CharField(max_length=50)

    def __str__(self):
        return self.part_name 


class Uav(models.Model):
    uav_id = models.AutoField(primary_key=True)
    uav_name = models.CharField(max_length=50)

    def __str__(self):
        return self.uav_name

class UavParts(models.Model):
    uav = models.ForeignKey(Uav, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)

class PartProduction(models.Model):
    part_production_id = models.AutoField(primary_key=True)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    uav = models.ForeignKey(Uav, on_delete=models.CASCADE, default=0)
    stock = models.IntegerField()
    
    PRODUCTION_TYPES = [
        ('MACHINE', 'Makine Üretimi'),
        ('CASTING', 'Döküm'),
        ('3D_PRINTING', '3D Baskı'),
        ('OTHER', 'Diğer'),
    ]
    
    PRODUCTION_MATERIALS = [
        ('ALUMINUM', 'Alüminyum'),
        ('COMPOSITE', 'Kompozit Malzeme'),
        ('TITANIUM', 'Titanyum'),
        ('PLASTIC', 'Plastik (Polymer)'),
        ('KEVLAR', 'Kevlar'),
        ('CERAMIC', 'Seramik'),
    ]
    
    production_type = models.CharField(
        max_length=20, 
        choices=PRODUCTION_TYPES, 
        default='MACHINE'
    )
    production_time = models.DateTimeField()
    material_type = models.CharField(
        max_length=100,
        choices=PRODUCTION_MATERIALS, 
        default='ALUMINUM'
    )
    length = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)



class Assembly(models.Model):
    assembly_id = models.AutoField(primary_key=True)
    uav = models.ForeignKey(Uav, on_delete=models.CASCADE)
    assembly_code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.assembly_code
    
class AssemblyPart(models.Model):
    assembly_part_id = models.AutoField(primary_key=True)
    assembly = models.ForeignKey(Assembly, on_delete=models.CASCADE)
    part_production = models.ForeignKey(PartProduction, on_delete=models.CASCADE, default=1)

class UavProduction(models.Model):
    assembly = models.ForeignKey(Assembly, on_delete=models.CASCADE)
    production_time = models.DateTimeField()
    part_count = models.IntegerField(default=0)