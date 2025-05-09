/**
 * مدیریت پیشرفته وضعیت املاک
 * سیستم هوشمند تغییر وضعیت با استفاده از AJAX
 */

class PropertyStatusManager {
    constructor() {
        this.init();
    }
    
    getCSRFToken() {
        // دریافت توکن CSRF از صفحه
        return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    }
    
    showError(message) {
        // نمایش پیام خطا به کاربر
        alert(message || 'خطایی در سیستم رخ داده است. لطفاً مجدداً تلاش کنید.');
    }
    
    showSuccess(message) {
        // نمایش پیام موفقیت به کاربر
        alert(message || 'عملیات با موفقیت انجام شد.');
    }
    
    changeStatus(propertyId, statusId, statusName) {
        // گرفتن توکن CSRF
        const csrfToken = this.getCSRFToken();
        if (!csrfToken) {
            this.showError('خطا در احراز هویت. لطفاً صفحه را مجدداً بارگذاری کنید.');
            return;
        }
        
        // تهیه داده‌های مورد نیاز برای ارسال
        const formData = new FormData();
        formData.append('status_id', statusId);
        
        // ارسال درخواست AJAX
        fetch(`/properties/change-status/${propertyId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`خطای سرور: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // بروزرسانی نمایش وضعیت
                const statusBadges = document.querySelectorAll(`[id^="property-status-${propertyId}"]`);
                
                statusBadges.forEach(statusBadge => {
                    // حذف کلاس‌های قبلی مرتبط با وضعیت
                    statusBadge.classList.remove(
                        'badge-available', 'badge-sold', 'badge-rented', 
                        'badge-reserved', 'badge-construction', 'badge-ready', 'badge-other'
                    );
                    
                    // اضافه کردن کلاس مناسب بر اساس وضعیت جدید
                    if (statusName === 'موجود') {
                        statusBadge.classList.add('badge-available');
                    } else if (statusName === 'فروخته شده') {
                        statusBadge.classList.add('badge-sold');
                    } else if (statusName === 'اجاره داده شده') {
                        statusBadge.classList.add('badge-rented');
                    } else if (statusName === 'رزرو شده') {
                        statusBadge.classList.add('badge-reserved');
                    } else if (statusName === 'در حال ساخت') {
                        statusBadge.classList.add('badge-construction');
                    } else if (statusName === 'آماده تحویل') {
                        statusBadge.classList.add('badge-ready');
                    } else {
                        statusBadge.classList.add('badge-other');
                    }
                    
                    // بروزرسانی متن و آیکون
                    let iconHTML = '';
                    if (statusName === 'موجود') {
                        iconHTML = '<i class="bi bi-check-circle-fill"></i>';
                    } else if (statusName === 'فروخته شده') {
                        iconHTML = '<i class="bi bi-currency-dollar"></i>';
                    } else if (statusName === 'اجاره داده شده') {
                        iconHTML = '<i class="bi bi-house-check-fill"></i>';
                    } else if (statusName === 'رزرو شده') {
                        iconHTML = '<i class="bi bi-bookmark-fill"></i>';
                    } else if (statusName === 'در حال ساخت') {
                        iconHTML = '<i class="bi bi-tools"></i>';
                    } else if (statusName === 'آماده تحویل') {
                        iconHTML = '<i class="bi bi-check2-all"></i>';
                    } else {
                        iconHTML = '<i class="bi bi-question-circle-fill"></i>';
                    }
                    statusBadge.innerHTML = iconHTML + ' ' + statusName;
                });
                
                // بروزرسانی کلاس فعال در تمام منوهای کشویی وضعیت این ملک
                document.querySelectorAll(`[id^="statusDropdown${propertyId}"] .status-option`).forEach(option => {
                    option.classList.remove('active');
                    if (option.getAttribute('data-status-id') === statusId) {
                        option.classList.add('active');
                    }
                });
                
                // نمایش پیام موفقیت
                this.showSuccess(`وضعیت ملک با موفقیت به «${statusName}» تغییر یافت.`);
            } else {
                // نمایش پیام خطا
                this.showError(data.message || 'خطای نامشخص در تغییر وضعیت ملک.');
            }
        })
        .catch(error => {
            console.error('Error changing property status:', error);
            this.showError('خطا در برقراری ارتباط با سرور. لطفاً مجدداً تلاش کنید.');
        });
    }
    
    init() {
        // راه‌اندازی گوش‌دهنده برای تغییر وضعیت‌ها
        document.addEventListener('DOMContentLoaded', () => {
            // بررسی همه گزینه‌های تغییر وضعیت در صفحه
            document.querySelectorAll('.status-option').forEach(option => {
                option.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    const propertyId = option.getAttribute('data-property-id');
                    const statusId = option.getAttribute('data-status-id');
                    const statusName = option.getAttribute('data-status-name');
                    
                    // تأیید تغییر وضعیت
                    if (confirm(`آیا از تغییر وضعیت این ملک به «${statusName}» اطمینان دارید؟`)) {
                        this.changeStatus(propertyId, statusId, statusName);
                    }
                });
            });
        });
    }
}

// راه‌اندازی مدیریت وضعیت‌ها
new PropertyStatusManager();