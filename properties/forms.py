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
