from django.contrib import admin
from DjangoAPI.models import Team,Employee,Part,Uav,UavParts

admin.site.register(Team)
admin.site.register(Part)
admin.site.register(Uav)
admin.site.register(UavParts)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'team', 'employee_sicil_no', 'password')  # Hangi alanların görüneceği
    readonly_fields = ('employee_sicil_no', 'password')  # Bu alanlar sadece görüntülenebilir
    search_fields = ('employee_name', 'employee_sicil_no')  # Arama yapılacak alanlar
    list_filter = ('team',)  # Filtreleme yapılacak alanlar

    def save_model(self, request, obj, form, change):
        # Şifre ve sicil numarasını admin üzerinden de otomatik oluşturulacak şekilde ayarlıyoruz
        if not obj.employee_sicil_no:
            obj.employee_sicil_no = obj.generate_sicil_no()
        
        if not obj.password:
            obj.password = obj.generate_random_password()

        super().save_model(request, obj, form, change)

admin.site.register(Employee, EmployeeAdmin)