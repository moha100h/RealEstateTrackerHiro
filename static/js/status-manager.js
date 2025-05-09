/**
 * مدیریت پیشرفته وضعیت املاک
 * سیستم هوشمند تغییر وضعیت با استفاده از AJAX
 */

class PropertyStatusManager {
    constructor() {
        // اطلاعات اصلی
        this.csrfToken = this.getCSRFToken();
        this.statusColors = {
            'موجود': 'success',
            'فروخته شده': 'danger',
            'اجاره داده شده': 'danger',
            'رزرو شده': 'warning',
            'در حال ساخت': 'info',
            'آماده تحویل': 'primary'
        };
        
        // مقداردهی اولیه
        this.init();
    }
    
    // دریافت توکن CSRF
    getCSRFToken() {
        return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    }
    
    // نمایش خطا
    showError(message) {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-danger alert-dismissible fade show';
        alertElement.innerHTML = `
            <i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="بستن"></button>
        `;
        
        // نمایش خطا در بالای صفحه
        const mainContainer = document.querySelector('main > .container');
        if (mainContainer) {
            mainContainer.insertBefore(alertElement, mainContainer.firstChild);
            
            // حذف خودکار بعد از 5 ثانیه
            setTimeout(() => {
                alertElement.remove();
            }, 5000);
        }
    }
    
    // نمایش پیام موفقیت
    showSuccess(message) {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-success alert-dismissible fade show';
        alertElement.innerHTML = `
            <i class="bi bi-check-circle-fill me-2"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="بستن"></button>
        `;
        
        // نمایش پیام در بالای صفحه
        const mainContainer = document.querySelector('main > .container');
        if (mainContainer) {
            mainContainer.insertBefore(alertElement, mainContainer.firstChild);
            
            // حذف خودکار بعد از 5 ثانیه
            setTimeout(() => {
                alertElement.remove();
            }, 5000);
        }
    }
    
    // تغییر وضعیت با AJAX
    changeStatus(propertyId, statusId, statusName) {
        // نمایش وضعیت در حال بارگذاری
        const statusBadge = document.querySelector(`#property-status-${propertyId}`);
        const statusCell = statusBadge.closest('td');
        const originalContent = statusCell.innerHTML;
        
        statusCell.innerHTML = `<div class="spinner-border spinner-border-sm text-primary" role="status">
                                    <span class="visually-hidden">در حال بارگذاری...</span>
                                </div>`;
        
        // ارسال درخواست به سرور
        fetch(`/properties/change-status/${propertyId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': this.csrfToken
            },
            body: `status_id=${statusId}`
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('خطا در ارتباط با سرور');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // بروزرسانی وضعیت در UI
                const colorClass = `bg-${this.statusColors[statusName] || 'secondary'}`;
                statusCell.innerHTML = `<span id="property-status-${propertyId}" class="badge ${colorClass}">${statusName}</span>`;
                
                // نمایش پیام موفقیت
                this.showSuccess(data.message);
                
                // بروزرسانی منوی وضعیت
                const statusDropdown = document.querySelector(`#statusDropdown${propertyId}`);
                if (statusDropdown) {
                    const activeItems = statusDropdown.querySelectorAll('.status-option.active');
                    activeItems.forEach(item => item.classList.remove('active'));
                    
                    const newActiveItem = statusDropdown.querySelector(`[data-status-id="${statusId}"]`);
                    if (newActiveItem) {
                        newActiveItem.classList.add('active');
                    }
                }
            } else {
                // نمایش خطا
                statusCell.innerHTML = originalContent;
                this.showError(data.message || 'خطا در تغییر وضعیت');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            statusCell.innerHTML = originalContent;
            this.showError(error.message);
        });
    }
    
    // مقداردهی اولیه و اتصال رویدادها
    init() {
        // اضافه کردن رویداد برای دکمه‌های تغییر وضعیت
        document.addEventListener('DOMContentLoaded', () => {
            // جستجوی همه منوهای تغییر وضعیت
            const statusItems = document.querySelectorAll('.status-option');
            statusItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    const propertyId = item.dataset.propertyId;
                    const statusId = item.dataset.statusId;
                    const statusName = item.dataset.statusName;
                    
                    // تغییر وضعیت با AJAX
                    this.changeStatus(propertyId, statusId, statusName);
                });
            });
        });
    }
}

// ایجاد نمونه از کلاس مدیریت وضعیت
const statusManager = new PropertyStatusManager();