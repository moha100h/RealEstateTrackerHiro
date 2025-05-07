/**
 * اسکریپت مدیریت تغییر وضعیت املاک
 * این اسکریپت وظیفه نمایش مودال تغییر وضعیت و ارسال درخواست‌های مربوطه را بر عهده دارد
 * نسخه: 1.0.0
 */

// اجرای کد پس از بارگذاری صفحه
document.addEventListener('DOMContentLoaded', function() {
    // متغیرهای مودال
    let currentPropertyId = null;
    const statusModal = document.getElementById('statusModal');
    const saveStatusBtn = document.getElementById('saveStatusBtn');
    
    // مطمئن شویم مودال و دکمه ذخیره وجود دارند
    if (!statusModal || !saveStatusBtn) {
        console.log('مودال تغییر وضعیت یا دکمه ذخیره پیدا نشد');
        return;
    }
    
    // ایجاد نمونه مودال با بوتسترپ
    const bsModal = new bootstrap.Modal(statusModal);
    
    // ذخیره تغییرات وضعیت با کلیک روی دکمه ذخیره
    saveStatusBtn.addEventListener('click', function() {
        const selectedStatus = document.querySelector('input[name="statusOption"]:checked');
        if (selectedStatus && currentPropertyId) {
            changePropertyStatus(currentPropertyId, selectedStatus.value);
            bsModal.hide();
        } else {
            showAlert('warning', 'لطفاً یک وضعیت را انتخاب کنید.');
        }
    });
    
    // تعریف تابع نمایش مودال به صورت عمومی برای استفاده در فایل HTML
    window.showStatusModal = function(propertyId, propertyTitle) {
        // ذخیره شناسه ملک فعلی
        currentPropertyId = propertyId;
        
        // نمایش عنوان ملک در مودال
        const titleElement = document.getElementById('propertyTitle');
        if (titleElement) {
            titleElement.textContent = propertyTitle;
        }
        
        // بررسی وضعیت فعلی ملک
        const statusBadge = document.getElementById(`status-badge-${propertyId}`);
        if (statusBadge) {
            const currentStatus = statusBadge.textContent.trim();
            
            // پاک کردن انتخاب‌های قبلی
            document.querySelectorAll('input[name="statusOption"]').forEach(radio => {
                radio.checked = false;
                
                // یافتن وضعیت فعلی و انتخاب آن
                const label = document.querySelector(`label[for="${radio.id}"]`);
                if (label && label.textContent.trim() === currentStatus) {
                    radio.checked = true;
                }
            });
        }
        
        // نمایش مودال
        bsModal.show();
    };
    
    // تابع ارسال درخواست تغییر وضعیت
    function changePropertyStatus(propertyId, statusId) {
        // گرفتن توکن CSRF از کوکی
        const csrftoken = getCookie('csrftoken');
        
        // ایجاد شیء FormData برای ارسال داده‌ها
        const formData = new FormData();
        formData.append('status_id', statusId);
        
        // نمایش وضعیت بارگذاری روی نشانگر وضعیت
        const statusBadge = document.getElementById(`status-badge-${propertyId}`);
        const originalContent = statusBadge.innerHTML;
        statusBadge.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">در حال بارگذاری...</span></div>';
        
        // ارسال درخواست تغییر وضعیت با متد صحیح
        // ارسال درخواست به آدرس صحیح API
        fetch(`/properties/change-status/${propertyId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // تغییر متن نشانگر وضعیت
                statusBadge.innerHTML = data.status_name;
                
                // تغییر کلاس نشانگر بر اساس وضعیت جدید
                let newClass = 'badge status-badge ';
                if (data.status_name === 'موجود') {
                    newClass += 'bg-success';
                } else if (data.status_name === 'فروخته شده' || data.status_name === 'اجاره داده شده') {
                    newClass += 'bg-danger';
                } else if (data.status_name === 'رزرو شده') {
                    newClass += 'bg-warning';
                } else if (data.status_name === 'در حال ساخت') {
                    newClass += 'bg-secondary';
                } else if (data.status_name === 'آماده تحویل') {
                    newClass += 'bg-info';
                } else {
                    newClass += 'bg-warning';
                }
                
                // اعمال کلاس جدید
                statusBadge.className = newClass;
                
                // نمایش پیام موفقیت‌آمیز
                showAlert('success', 'وضعیت ملک با موفقیت تغییر کرد.');
            } else {
                // بازگرداندن وضعیت قبلی در صورت خطا
                statusBadge.innerHTML = originalContent;
                
                // نمایش پیام خطا
                showAlert('danger', data.message || 'خطایی در تغییر وضعیت رخ داد.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // بازگرداندن وضعیت قبلی در صورت خطا
            statusBadge.innerHTML = originalContent;
            
            // نمایش پیام خطا
            showAlert('danger', 'خطایی در ارتباط با سرور رخ داد.');
        });
    }
    
    // تابع دریافت توکن CSRF از کوکی
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {
                const cookieTrim = cookie.trim();
                if (cookieTrim.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookieTrim.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // تابع نمایش هشدار
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show my-3`;
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.property-content');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // حذف خودکار هشدار پس از چند ثانیه
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 500);
            }, 3000);
        }
    }
});