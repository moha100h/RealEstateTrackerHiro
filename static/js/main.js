// اسکریپت‌های عمومی سیستم مدیریت املاک هیرو

// اجرای کد پس از لود شدن صفحه
document.addEventListener('DOMContentLoaded', function() {
    // فعال‌سازی تولتیپ‌ها
    initTooltips();
    
    // فعال‌سازی المان‌های select2 در صورت وجود
    initSelect2();
    
    // فرمت کردن اعداد فارسی
    formatPersianNumbers();
    
    // نمایش پیش‌نمایش تصاویر در هنگام آپلود
    setupImagePreview();
    
    // اضافه کردن مدیریت بسته شدن خودکار alert‌ها
    setupAlertDismiss();
    
    // مدیریت منوی موبایل
    setupMobileMenu();
    
    // مدیریت فیلترهای جستجو در صفحه جستجوی پیشرفته
    setupFilterToggle();
    
    // نمایش تاییدیه قبل از حذف
    setupDeleteConfirmation();
});

// فعال‌سازی تولتیپ‌ها
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// فعال‌سازی select2 در صورت استفاده از این کتابخانه
function initSelect2() {
    if (typeof($.fn.select2) !== 'undefined') {
        $('.select2').select2({
            dir: 'rtl',
            language: 'fa'
        });
    }
}

// تبدیل اعداد لاتین به فارسی
function formatPersianNumbers() {
    const persianNumbers = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    
    document.querySelectorAll('.persian-number').forEach(function(el) {
        let text = el.textContent;
        for (let i = 0; i < 10; i++) {
            text = text.replace(new RegExp(i, 'g'), persianNumbers[i]);
        }
        el.textContent = text;
    });
}

// نمایش پیش‌نمایش تصاویر در هنگام آپلود
function setupImagePreview() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                
                // پیدا کردن مکان نمایش پیش‌نمایش (معمولاً یک div یا img با کلاس preview بعد از input)
                const previewElement = input.nextElementSibling?.classList.contains('preview') 
                    ? input.nextElementSibling 
                    : document.querySelector(`#${input.id}-preview`);
                
                if (previewElement) {
                    reader.onload = function(e) {
                        if (previewElement.tagName === 'IMG') {
                            previewElement.src = e.target.result;
                            previewElement.style.display = 'block';
                        } else {
                            // اگر یک div است، یک تصویر داخلش ایجاد می‌کنیم
                            previewElement.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px;">`;
                            previewElement.style.display = 'block';
                        }
                    };
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    });
}

// مدیریت بسته شدن خودکار هشدارها
function setupAlertDismiss() {
    // هشدارهایی که کلاس auto-dismiss را دارند، بعد از 5 ثانیه به طور خودکار بسته می‌شوند
    document.querySelectorAll('.alert.auto-dismiss').forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                alert.classList.remove('show');
                setTimeout(function() {
                    alert.remove();
                }, 150);
            }
        }, 5000);
    });
}

// مدیریت منوی موبایل
function setupMobileMenu() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
    }
}

// تاگل نمایش/مخفی کردن فیلترهای جستجو در موبایل
function setupFilterToggle() {
    const filterToggleBtn = document.querySelector('.filter-toggle');
    const filtersContainer = document.querySelector('.filters-container');
    
    if (filterToggleBtn && filtersContainer) {
        filterToggleBtn.addEventListener('click', function() {
            filtersContainer.classList.toggle('d-none');
            filterToggleBtn.textContent = filtersContainer.classList.contains('d-none') 
                ? 'نمایش فیلترها' 
                : 'پنهان کردن فیلترها';
        });
    }
}

// پرسیدن تاییدیه قبل از حذف موارد
function setupDeleteConfirmation() {
    document.querySelectorAll('.delete-confirm').forEach(function(element) {
        element.addEventListener('click', function(event) {
            if (!confirm('آیا از حذف این مورد اطمینان دارید؟ این عملیات قابل برگشت نیست.')) {
                event.preventDefault();
            }
        });
    });
}

// فعال کردن یا غیرفعال کردن دکمه ارسال فرم
function toggleSubmitButton(formId, isDisabled) {
    const form = document.getElementById(formId);
    if (form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = isDisabled;
            
            // تغییر متن دکمه در حالت‌های مختلف
            if (isDisabled) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> در حال پردازش...';
            } else {
                // بازگرداندن متن اصلی دکمه
                const originalText = submitButton.getAttribute('data-original-text') || 'ذخیره';
                submitButton.innerHTML = originalText;
            }
        }
    }
}

// تابع فرمت‌کردن قیمت به صورت سه رقم سه رقم
function formatPrice(price) {
    return new Intl.NumberFormat('fa-IR').format(price);
}

// تابع کوتاه کردن متن با افزودن سه نقطه در انتها
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// نمایش یا مخفی کردن یک المان با انیمیشن
function toggleElement(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        if (show) {
            element.style.display = 'block';
            element.classList.add('fade-in');
        } else {
            element.style.display = 'none';
            element.classList.remove('fade-in');
        }
    }
}

// ارسال فرم با AJAX برای جلوگیری از رفرش صفحه
function submitFormAjax(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // غیرفعال کردن دکمه ارسال
        toggleSubmitButton(formId, true);
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // فعال کردن دکمه ارسال
            toggleSubmitButton(formId, false);
            
            if (successCallback && typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => {
            // فعال کردن دکمه ارسال
            toggleSubmitButton(formId, false);
            
            if (errorCallback && typeof errorCallback === 'function') {
                errorCallback(error);
            } else {
                console.error('خطا در ارسال فرم:', error);
                alert('خطا در ارسال اطلاعات. لطفاً دوباره تلاش کنید.');
            }
        });
    });
}
