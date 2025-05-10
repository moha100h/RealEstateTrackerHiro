from django import forms
from django.core.files.base import ContentFile
from django.forms import ClearableFileInput
from .models import Property, PropertyType, TransactionType, PropertyStatus, DocumentType, PropertyImage

class MultipleFileInput(ClearableFileInput):
    """ویجت آپلود چندین فایل"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """فیلد آپلود چندین فایل"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class PropertyForm(forms.ModelForm):
    """فرم ثبت و ویرایش ملک"""
    additional_images = MultipleFileField(
        label="تصاویر اضافی",
        required=False,
        help_text="می‌توانید چندین تصویر را انتخاب کنید. (برای انتخاب چندین تصویر، کلید Ctrl را نگه دارید)"
    )
    
    class Meta:
        model = Property
        fields = [
            'title', 'address', 'area', 'price', 'year_built',
            'property_type', 'transaction_type', 'status', 'document_type',
            'rooms', 'description', 'owner_contact', 'image',
            'has_elevator', 'has_parking', 'has_warehouse', 'has_balcony',
            'is_renovated', 'has_package', 'latitude', 'longitude'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'owner_contact': forms.TextInput(attrs={'placeholder': 'نام، شماره تماس و ایمیل مالک'}),
            'year_built': forms.NumberInput(attrs={'min': 1300, 'max': 1410}),
            'area': forms.NumberInput(attrs={'min': 1}),
            'price': forms.NumberInput(attrs={'min': 0}),
            'rooms': forms.NumberInput(attrs={'min': 0, 'max': 20}),
            'has_elevator': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_warehouse': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_balcony': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_renovated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_package': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'مثال: 35.7219'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': 'مثال: 51.3347'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # افزودن کلاس‌های بوتسترپ به فرم‌ها
        for field_name, field in self.fields.items():
            # برای چک‌باکس‌ها کلاس متفاوت اعمال می‌شود
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
                
        # توضیحات بیشتر برای فیلدهای جدید
        self.fields['owner_contact'].help_text = 'اطلاعات تماس مالک ملک، مانند نام، شماره تماس و ایمیل (اختیاری)'
        self.fields['latitude'].help_text = 'مختصات جغرافیایی برای نمایش روی نقشه (اختیاری)'
        self.fields['longitude'].help_text = 'مختصات جغرافیایی برای نمایش روی نقشه (اختیاری)'
    
    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        # ذخیره تصاویر اضافی
        additional_images = self.cleaned_data.get('additional_images', None)
        if additional_images:
            for order, image in enumerate(additional_images):
                PropertyImage.objects.create(
                    property=instance,
                    image=image,
                    order=order
                )
        
        return instance
