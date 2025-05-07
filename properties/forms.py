from django import forms
from .models import Property, PropertyType, TransactionType, PropertyStatus

class PropertyForm(forms.ModelForm):
    """فرم ثبت و ویرایش ملک"""
    
    class Meta:
        model = Property
        fields = [
            'title', 'address', 'area', 'price', 'year_built',
            'property_type', 'transaction_type', 'status',
            'rooms', 'description', 'image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'year_built': forms.NumberInput(attrs={'min': 1300, 'max': 1410}),
            'area': forms.NumberInput(attrs={'min': 1}),
            'price': forms.NumberInput(attrs={'min': 0}),
            'rooms': forms.NumberInput(attrs={'min': 0, 'max': 20}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ به فرم‌ها
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
