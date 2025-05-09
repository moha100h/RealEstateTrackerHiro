/**
 * مدیریت وضعیت املاک - نسخه 2.0.0
 * سیستم املاک هیرو - پیشرفته
 * فایل اصلاح شده برای استفاده در صفحه جستجو
 */

document.addEventListener('DOMContentLoaded', function() {
    // متغیرهای سراسری
    let currentPropertyId = null;
    let propertyTitle = null;
    
    // ساخت مودال به صورت پویا
    function createOrUpdateStatusModal() {
        // بررسی وجود مودال
        let statusModal = document.getElementById('statusChangeModal');
        
        // اگر مودال وجود ندارد، آن را ایجاد میکنیم
        if (!statusModal) {
            statusModal = document.createElement('div');
            statusModal.id = 'statusChangeModal';
            statusModal.className = 'modal fade';
            statusModal.tabIndex = -1;
            statusModal.setAttribute('aria-labelledby', 'statusChangeModalLabel');
            statusModal.setAttribute('aria-hidden', 'true');
            
            // ساختار داخلی مودال
            statusModal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header border-0">
                            <h5 class="modal-title" id="statusChangeModalLabel">تغییر وضعیت ملک</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body pt-0">
                            <h6 id="property-title-display" class="mb-4 text-muted fs-6"></h6>
                            
                            <div class="status-selector mb-4">
                                <div class="row g-3">
                                    <div class="col-6 col-md-4">
                                        <div class="status-option available" data-status-id="1">
                                            <input type="radio" name="statusOption" id="status1" value="1" class="status-radio visually-hidden">
                                            <label for="status1" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check-circle"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                                                </span>
                                                <span class="status-text">موجود</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="status-option sold" data-status-id="2">
                                            <input type="radio" name="statusOption" id="status2" value="2" class="status-radio visually-hidden">
                                            <label for="status2" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-dollar-sign"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                                                </span>
                                                <span class="status-text">فروخته شده</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="status-option rented" data-status-id="3">
                                            <input type="radio" name="statusOption" id="status3" value="3" class="status-radio visually-hidden">
                                            <label for="status3" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-key"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg>
                                                </span>
                                                <span class="status-text">اجاره داده شده</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="status-option reserved" data-status-id="4">
                                            <input type="radio" name="statusOption" id="status4" value="4" class="status-radio visually-hidden">
                                            <label for="status4" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bookmark"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
                                                </span>
                                                <span class="status-text">رزرو شده</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="status-option building" data-status-id="5">
                                            <input type="radio" name="statusOption" id="status5" value="5" class="status-radio visually-hidden">
                                            <label for="status5" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-tool"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path></svg>
                                                </span>
                                                <span class="status-text">در حال ساخت</span>
                                            </label>
                                        </div>
                                    </div>
                                    <div class="col-6 col-md-4">
                                        <div class="status-option ready" data-status-id="6">
                                            <input type="radio" name="statusOption" id="status6" value="6" class="status-radio visually-hidden">
                                            <label for="status6" class="status-label p-3 rounded-3 text-center w-100 h-100 d-flex flex-column align-items-center justify-content-center">
                                                <span class="status-icon mb-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-package"><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                                                </span>
                                                <span class="status-text">آماده تحویل</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="form-group mb-3" id="description-container">
                                <label for="status-description" class="form-label">توضیحات (اختیاری):</label>
                                <textarea id="status-description" class="form-control" rows="2"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer border-0 pt-0">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">انصراف</button>
                            <button type="button" id="saveStatusBtn" class="btn btn-primary">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true" id="statusSpinner"></span>
                                <span id="saveButtonText">ذخیره تغییرات</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // افزودن مودال به بدنه صفحه
            document.body.appendChild(statusModal);
            
            // افزودن استایل‌های مودال
            addModalStyles();
        }
        
        return statusModal;
    }
    
    // افزودن استایل‌های موردنیاز برای مودال
    function addModalStyles() {
        if (document.getElementById('status-modal-styles')) return;
        
        const styleElement = document.createElement('style');
        styleElement.id = 'status-modal-styles';
        styleElement.textContent = `
            .status-label {
                cursor: pointer;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                height: 100%;
            }
            
            .status-label:hover {
                border-color: #ced4da;
                transform: translateY(-2px);
            }
            
            .status-radio:checked + .status-label {
                border-width: 2px;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            }
            
            .available .status-label {
                color: #198754;
            }
            
            .sold .status-label, .rented .status-label {
                color: #dc3545;
            }
            
            .reserved .status-label {
                color: #fd7e14;
            }
            
            .building .status-label {
                color: #6c757d;
            }
            
            .ready .status-label {
                color: #0d6efd;
            }
            
            .status-radio:checked + .available .status-label,
            .available .status-radio:checked + .status-label {
                background-color: rgba(25, 135, 84, 0.1);
                border-color: #198754;
            }
            
            .status-radio:checked + .sold .status-label,
            .sold .status-radio:checked + .status-label,
            .status-radio:checked + .rented .status-label,
            .rented .status-radio:checked + .status-label {
                background-color: rgba(220, 53, 69, 0.1);
                border-color: #dc3545;
            }
            
            .status-radio:checked + .reserved .status-label,
            .reserved .status-radio:checked + .status-label {
                background-color: rgba(253, 126, 20, 0.1);
                border-color: #fd7e14;
            }
            
            .status-radio:checked + .building .status-label,
            .building .status-radio:checked + .status-label {
                background-color: rgba(108, 117, 125, 0.1);
                border-color: #6c757d;
            }
            
            .status-radio:checked + .ready .status-label,
            .ready .status-radio:checked + .status-label {
                background-color: rgba(13, 110, 253, 0.1);
                border-color: #0d6efd;
            }
            
            .status-icon {
                font-size: 1.5rem;
            }
            
            .status-text {
                font-weight: 500;
            }
            
            @media (max-width: 767.98px) {
                .status-icon {
                    font-size: 1.25rem;
                }
                .status-text {
                    font-size: 0.875rem;
                }
            }
            
            .hover-float {
                transition: transform 0.3s ease;
            }
            
            .hover-float:hover {
                transform: translateY(-5px);
            }
        `;
        
        document.head.appendChild(styleElement);
    }
    
    // نمایش مودال تغییر وضعیت
    window.showStatusModal = function(id, title) {
        // ذخیره اطلاعات ملک فعلی
        currentPropertyId = id;
        propertyTitle = title;
        
        console.log("نمایش مودال تغییر وضعیت برای ملک:", id, title);
        
        // بررسی وجود مودال پیش‌فرض صفحه
        const staticModal = document.getElementById('statusChangeModal');
        
        if (staticModal) {
            console.log("استفاده از مودال استاتیک موجود");
            
            // نمایش عنوان ملک در مودال استاتیک
            const propertyTitleElem = document.getElementById('propertyTitle');
            if (propertyTitleElem) {
                propertyTitleElem.textContent = title;
            }
            
            // پیدا کردن وضعیت فعلی ملک
            const statusBadge = document.getElementById(`status-badge-${id}`) || 
                              document.getElementById(`status-badge-mobile-${id}`);
            
            if (statusBadge) {
                const currentStatus = statusBadge.textContent.trim();
                
                // انتخاب گزینه مناسب در سلکت باکس
                const statusSelect = document.getElementById('statusSelect');
                if (statusSelect) {
                    for (let i = 0; i < statusSelect.options.length; i++) {
                        if (statusSelect.options[i].text === currentStatus) {
                            statusSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            }
            
            // اضافه کردن رویداد به دکمه ذخیره
            const saveBtn = document.getElementById('saveStatusBtn');
            if (saveBtn) {
                // حذف همه رویدادهای قبلی
                const newSaveBtn = saveBtn.cloneNode(true);
                saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
                
                // اضافه کردن رویداد جدید
                newSaveBtn.addEventListener('click', function() {
                    const statusSelect = document.getElementById('statusSelect');
                    const selectedStatusId = statusSelect.value;
                    changePropertyStatus(id, selectedStatusId);
                    
                    // بستن مودال
                    const modal = bootstrap.Modal.getInstance(staticModal);
                    modal.hide();
                });
            }
            
            // ایجاد نمونه مودال با بوتسترپ و نمایش آن
            const bsModal = new bootstrap.Modal(staticModal);
            bsModal.show();
            
            return;
        }
        
        // اگر مودال استاتیک پیدا نشد، مودال پویا ایجاد می‌کنیم
        console.log("ایجاد مودال پویا");
        const statusModal = createOrUpdateStatusModal();
        
        // نمایش عنوان ملک در مودال
        const titleDisplay = document.getElementById('property-title-display');
        if (titleDisplay) {
            titleDisplay.textContent = title;
        }
        
        // پیدا کردن وضعیت فعلی ملک
        const statusBadge = document.getElementById(`status-badge-${id}`) || 
                          document.getElementById(`status-badge-mobile-${id}`);
        
        if (statusBadge) {
            const currentStatus = statusBadge.textContent.trim();
            
            // انتخاب گزینه مناسب بر اساس وضعیت فعلی
            document.querySelectorAll('input[name="statusOption"]').forEach(radio => {
                radio.checked = false;
                
                const label = document.querySelector(`label[for="${radio.id}"]`);
                const statusText = label.querySelector('.status-text').textContent.trim();
                
                if (statusText === currentStatus) {
                    radio.checked = true;
                }
            });
        }
        
        // پاک کردن توضیحات قبلی
        const descriptionInput = document.getElementById('status-description');
        if (descriptionInput) {
            descriptionInput.value = '';
        }
        
        // پاک کردن وضعیت قبلی دکمه
        resetSaveButton();
        
        // ایجاد نمونه مودال با بوتسترپ و نمایش آن
        const bsModal = new bootstrap.Modal(statusModal);
        bsModal.show();
        
        // اضافه کردن رویداد به دکمه ذخیره
        const saveButton = document.getElementById('saveStatusBtn');
        if (saveButton) {
            // حذف رویدادهای قبلی برای جلوگیری از تکرار
            saveButton.replaceWith(saveButton.cloneNode(true));
            
            // افزودن رویداد جدید
            document.getElementById('saveStatusBtn').addEventListener('click', handleStatusChange);
        }
    };
    
    // بازنشانی وضعیت دکمه ذخیره
    function resetSaveButton() {
        const saveButton = document.getElementById('saveStatusBtn');
        const spinner = document.getElementById('statusSpinner');
        const buttonText = document.getElementById('saveButtonText');
        
        if (saveButton && spinner && buttonText) {
            saveButton.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'ذخیره تغییرات';
        }
    }
    
    // مدیریت تغییر وضعیت
    function handleStatusChange() {
        const selectedOption = document.querySelector('input[name="statusOption"]:checked');
        
        if (!selectedOption || !currentPropertyId) {
            showNotification('warning', 'لطفاً یک وضعیت را انتخاب کنید.');
            return;
        }
        
        // فعال کردن وضعیت بارگذاری دکمه
        const saveButton = document.getElementById('saveStatusBtn');
        const spinner = document.getElementById('statusSpinner');
        const buttonText = document.getElementById('saveButtonText');
        
        if (saveButton && spinner && buttonText) {
            saveButton.disabled = true;
            spinner.classList.remove('d-none');
            buttonText.textContent = 'در حال ذخیره...';
        }
        
        // دریافت توضیحات (اگر وارد شده باشد)
        const description = document.getElementById('status-description').value.trim();
        
        // اعمال تغییر وضعیت
        changePropertyStatus(currentPropertyId, selectedOption.value, description);
    }
    
    // تغییر وضعیت ملک
    function changePropertyStatus(propertyId, statusId, description = '') {
        // دریافت توکن CSRF
        const csrftoken = getCookie('csrftoken');
        
        // ایجاد داده‌های فرم
        const formData = new FormData();
        formData.append('status_id', statusId);
        if (description) {
            formData.append('description', description);
        }
        
        // نمایش وضعیت بارگذاری در نشانگرهای وضعیت
        const statusBadge = document.getElementById(`status-badge-${propertyId}`);
        const mobileBadge = document.getElementById(`status-badge-mobile-${propertyId}`);
        
        // ذخیره محتوای اصلی
        const originalContent = statusBadge ? statusBadge.innerHTML : '';
        const originalMobileContent = mobileBadge ? mobileBadge.innerHTML : '';
        
        // نمایش اسپینر بارگذاری
        const loaderHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">در حال بارگذاری...</span></div>';
        if (statusBadge) statusBadge.innerHTML = loaderHTML;
        if (mobileBadge) mobileBadge.innerHTML = loaderHTML;
        
        // ارسال درخواست تغییر وضعیت
        fetch(`/properties/change-status/${propertyId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
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
                // به‌روزرسانی نشانگرهای وضعیت
                updateStatusBadges(propertyId, data.status_name);
                
                // بستن مودال
                const modal = bootstrap.Modal.getInstance(document.getElementById('statusChangeModal'));
                if (modal) modal.hide();
                
                // نمایش اعلان موفقیت
                showNotification('success', 'وضعیت ملک با موفقیت تغییر کرد.');
            } else {
                // بازگرداندن وضعیت قبلی در صورت خطا
                if (statusBadge) statusBadge.innerHTML = originalContent;
                if (mobileBadge) mobileBadge.innerHTML = originalMobileContent;
                
                // بازنشانی دکمه ذخیره
                resetSaveButton();
                
                // نمایش اعلان خطا
                showNotification('danger', data.message || 'خطایی در تغییر وضعیت رخ داد.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // بازگرداندن وضعیت قبلی در صورت خطا
            if (statusBadge) statusBadge.innerHTML = originalContent;
            if (mobileBadge) mobileBadge.innerHTML = originalMobileContent;
            
            // بازنشانی دکمه ذخیره
            resetSaveButton();
            
            // نمایش اعلان خطا
            showNotification('danger', 'خطایی در ارتباط با سرور رخ داد.');
        });
    }
    
    // به‌روزرسانی نشانگرهای وضعیت
    function updateStatusBadges(propertyId, statusName) {
        // تعیین کلاس مناسب بر اساس نام وضعیت
        let badgeClass = getBadgeClassForStatus(statusName);
        
        // به‌روزرسانی نشانگر وضعیت در نمای دسکتاپ
        const statusBadge = document.getElementById(`status-badge-${propertyId}`);
        if (statusBadge) {
            statusBadge.innerHTML = statusName;
            statusBadge.className = `badge ${badgeClass} status-badge fw-medium`;
        }
        
        // به‌روزرسانی نشانگر وضعیت در نمای موبایل
        const mobileBadge = document.getElementById(`status-badge-mobile-${propertyId}`);
        if (mobileBadge) {
            mobileBadge.innerHTML = statusName;
            mobileBadge.className = `badge ${badgeClass} position-absolute top-0 start-0 m-2`;
        }
    }
    
    // تعیین کلاس CSS برای نشانگر وضعیت
    function getBadgeClassForStatus(statusName) {
        switch (statusName) {
            case 'موجود':
                return 'bg-success';
            case 'فروخته شده':
            case 'اجاره داده شده':
                return 'bg-danger';
            case 'رزرو شده':
                return 'bg-primary';
            case 'در حال ساخت':
                return 'bg-secondary';
            case 'آماده تحویل':
                return 'bg-info';
            default:
                return 'bg-warning';
        }
    }
    
    // نمایش اعلان به کاربر
    function showNotification(type, message) {
        // بررسی وجود کانتینر برای اعلان‌ها
        let container = document.querySelector('.notification-container');
        
        // اگر کانتینر وجود ندارد، ایجاد می‌کنیم
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        
        // ایجاد اعلان
        const notificationId = 'notification-' + Date.now();
        const notification = document.createElement('div');
        notification.id = notificationId;
        notification.className = `toast align-items-center text-white bg-${type} border-0`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        
        notification.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        // افزودن اعلان به کانتینر
        container.appendChild(notification);
        
        // نمایش اعلان
        const toast = new bootstrap.Toast(notification, {
            autohide: true,
            delay: 4000
        });
        toast.show();
        
        // حذف اعلان پس از بسته شدن
        notification.addEventListener('hidden.bs.toast', function() {
            notification.remove();
        });
    }
    
    // دریافت توکن CSRF از کوکی
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
    
    // مقداردهی اولیه
    function initialize() {
        // آماده سازی مودال - فقط تنظیم استایل‌ها برای آماده بودن
        addModalStyles();
        
        // اضافه کردن رویداد کلیک به همه دکمه‌های تغییر وضعیت
        document.querySelectorAll('[onclick*="showStatusModal"]').forEach(button => {
            button.classList.add('hover-float');
        });
    }
    
    // شروع
    initialize();
});