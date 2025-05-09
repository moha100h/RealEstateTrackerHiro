/**
 * مدیریت حرفه‌ای تغییر وضعیت املاک
 * توسعه داده شده برای سیستم هیرو املاک
 */

// متغیرها و اشیاء سراسری
const StatusManager = {
    currentPropertyId: null,
    propertyTitle: null,
    statusOptions: {},
    modalElement: null,
    modalInstance: null,
    
    // مقداردهی اولیه و راه‌اندازی سیستم
    init: function() {
        console.log("راه‌اندازی مدیریت وضعیت املاک");
        
        // افزودن استایل‌های CSS مورد نیاز
        this.addRequiredStyles();
        
        // بستن مودال با کلیک خارج از آن
        document.addEventListener('click', function(e) {
            if (StatusManager.modalElement && 
                !StatusManager.modalElement.contains(e.target) && 
                e.target.id !== 'status-badge' &&
                !e.target.classList.contains('property-link') &&
                !e.target.closest('.property-link')) {
                StatusManager.closeModal();
            }
        });
        
        // جلوگیری از انتشار کلیک درون مودال به بیرون
        document.addEventListener('click', function(e) {
            const modal = document.querySelector('.status-modal-container');
            if (modal && modal.contains(e.target)) {
                e.stopPropagation();
            }
        }, true);
    },
    
    // نمایش مودال تغییر وضعیت
    showModal: function(propertyId, title) {
        console.log("نمایش مودال برای ملک:", propertyId, title);
        
        // ذخیره اطلاعات ملک فعلی
        this.currentPropertyId = propertyId;
        this.propertyTitle = title;
        
        // بستن مودال قبلی اگر باز است
        this.closeModal();
        
        // ایجاد مودال جدید
        this.createModal();
        
        // یافتن وضعیت فعلی ملک
        const statusElement = document.getElementById(`status-badge-${propertyId}`) || 
                            document.getElementById(`status-badge-mobile-${propertyId}`);
        
        let currentStatus = '';
        if (statusElement) {
            currentStatus = statusElement.textContent.trim();
        }
        
        // پر کردن اطلاعات مودال
        const titleElement = document.getElementById('status-property-title');
        if (titleElement) titleElement.textContent = title;
        
        // انتخاب وضعیت فعلی در گزینه‌ها
        const optionElements = document.querySelectorAll('.status-option');
        optionElements.forEach(option => {
            const statusName = option.getAttribute('data-status-name');
            if (statusName === currentStatus) {
                option.classList.add('active');
            }
        });
        
        // نمایش مودال
        this.showModalElement();
    },
    
    // ایجاد مودال به صورت پویا
    createModal: function() {
        // ایجاد کانتینر اصلی
        const modalContainer = document.createElement('div');
        modalContainer.className = 'status-modal-container';
        this.modalElement = modalContainer;
        
        // ساختار HTML مودال
        modalContainer.innerHTML = `
            <div class="status-modal shadow-lg">
                <div class="status-modal-header">
                    <h5>تغییر وضعیت ملک</h5>
                    <button type="button" class="status-close-btn" id="closeStatusModalBtn">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
                <div class="status-modal-body">
                    <div class="status-property-info mb-4">
                        <div class="status-property-label">عنوان ملک:</div>
                        <div class="status-property-value" id="status-property-title"></div>
                    </div>
                    
                    <div class="status-options-container">
                        <div class="status-options-label">انتخاب وضعیت جدید:</div>
                        <div class="status-options" id="statusOptionsList">
                            ${this.generateStatusOptions()}
                        </div>
                    </div>
                </div>
                <div class="status-modal-footer">
                    <button type="button" class="status-cancel-btn" id="cancelStatusBtn">انصراف</button>
                    <button type="button" class="status-save-btn" id="saveStatusChangeBtn">
                        <span class="btn-text">ذخیره تغییرات</span>
                        <span class="btn-spinner d-none">
                            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        </span>
                    </button>
                </div>
            </div>
        `;
        
        // افزودن به DOM
        document.body.appendChild(modalContainer);
        
        // اضافه کردن کلاس انیمیشن با تأخیر (برای نمایش انیمیشن)
        setTimeout(() => {
            modalContainer.classList.add('show');
        }, 10);
        
        // اضافه کردن رویدادها
        this.setupEventListeners();
    },
    
    // تولید گزینه‌های وضعیت
    generateStatusOptions: function() {
        // خوانش وضعیت‌ها از فرم‌های موجود در صفحه
        const statusSelect = document.getElementById('statusSelect');
        let options = '';
        this.statusOptions = {};
        
        if (statusSelect) {
            Array.from(statusSelect.options).forEach(option => {
                const statusId = option.value;
                const statusName = option.textContent.trim();
                this.statusOptions[statusName] = statusId;
                
                const badgeClass = this.getBadgeClassForStatus(statusName);
                options += `
                    <div class="status-option" data-status-id="${statusId}" data-status-name="${statusName}">
                        <span class="status-badge ${badgeClass}">${statusName}</span>
                    </div>
                `;
            });
        } else {
            // وضعیت‌های پیش‌فرض اگر دراپ‌داون در صفحه وجود نداشت
            const defaultStatuses = [
                {id: 1, name: 'موجود', class: 'bg-success'},
                {id: 2, name: 'فروخته شده', class: 'bg-danger'},
                {id: 3, name: 'اجاره داده شده', class: 'bg-danger'},
                {id: 4, name: 'رزرو شده', class: 'bg-primary'},
                {id: 5, name: 'در حال ساخت', class: 'bg-secondary'},
                {id: 6, name: 'آماده تحویل', class: 'bg-warning'},
            ];
            
            defaultStatuses.forEach(status => {
                this.statusOptions[status.name] = status.id;
                options += `
                    <div class="status-option" data-status-id="${status.id}" data-status-name="${status.name}">
                        <span class="status-badge ${status.class}">${status.name}</span>
                    </div>
                `;
            });
        }
        
        return options;
    },
    
    // تعیین کلاس CSS برای نشانگر وضعیت
    getBadgeClassForStatus: function(statusName) {
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
                return 'bg-warning';
            default:
                return 'bg-secondary';
        }
    },
    
    // راه‌اندازی رویدادها
    setupEventListeners: function() {
        // دکمه بستن
        const closeBtn = document.getElementById('closeStatusModalBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeModal());
        }
        
        // دکمه انصراف
        const cancelBtn = document.getElementById('cancelStatusBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }
        
        // دکمه ذخیره
        const saveBtn = document.getElementById('saveStatusChangeBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveStatus());
        }
        
        // انتخاب گزینه‌های وضعیت
        const options = document.querySelectorAll('.status-option');
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                // حذف کلاس فعال از همه گزینه‌ها
                options.forEach(opt => opt.classList.remove('active'));
                // افزودن کلاس فعال به گزینه انتخاب شده
                option.classList.add('active');
            });
        });
    },
    
    // نمایش مودال
    showModalElement: function() {
        if (this.modalElement) {
            this.modalElement.style.display = 'flex';
            
            // اضافه کردن کلاس نمایش با تأخیر (برای نمایش انیمیشن)
            setTimeout(() => {
                this.modalElement.classList.add('show');
            }, 10);
        }
    },
    
    // بستن مودال
    closeModal: function() {
        const existingModal = document.querySelector('.status-modal-container');
        if (existingModal) {
            existingModal.classList.remove('show');
            
            // حذف مودال از DOM پس از پایان انیمیشن
            setTimeout(() => {
                existingModal.remove();
                this.modalElement = null;
            }, 300);
        }
    },
    
    // ذخیره تغییر وضعیت
    saveStatus: function() {
        // یافتن گزینه انتخاب شده
        const selectedOption = document.querySelector('.status-option.active');
        if (!selectedOption) {
            this.showNotification('لطفاً یک وضعیت را انتخاب کنید', 'warning');
            return;
        }
        
        const statusId = selectedOption.getAttribute('data-status-id');
        const statusName = selectedOption.getAttribute('data-status-name');
        
        // نمایش وضعیت بارگذاری
        this.setSaveButtonLoading(true);
        
        // ذخیره نشانگرهای وضعیت فعلی برای بازیابی در صورت خطا
        const statusBadge = document.getElementById(`status-badge-${this.currentPropertyId}`);
        const mobileBadge = document.getElementById(`status-badge-mobile-${this.currentPropertyId}`);
        
        // ذخیره محتوای اصلی
        const originalContent = statusBadge ? statusBadge.innerHTML : '';
        const originalMobileContent = mobileBadge ? mobileBadge.innerHTML : '';
        
        // نمایش اسپینر بارگذاری در نشانگرهای وضعیت
        const loaderHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">در حال بارگذاری...</span></div>';
        if (statusBadge) statusBadge.innerHTML = loaderHTML;
        if (mobileBadge) mobileBadge.innerHTML = loaderHTML;
        
        // ارسال درخواست تغییر وضعیت
        this.sendStatusChangeRequest(this.currentPropertyId, statusId)
            .then(data => {
                if (data.success) {
                    // به‌روزرسانی نشانگرهای وضعیت
                    this.updateStatusBadges(this.currentPropertyId, data.status_name);
                    
                    // بستن مودال
                    this.closeModal();
                    
                    // نمایش اعلان موفقیت
                    this.showNotification('وضعیت ملک با موفقیت تغییر کرد', 'success');
                } else {
                    // بازگرداندن وضعیت قبلی در صورت خطا
                    if (statusBadge) statusBadge.innerHTML = originalContent;
                    if (mobileBadge) mobileBadge.innerHTML = originalMobileContent;
                    
                    // نمایش اعلان خطا
                    this.showNotification(data.message || 'خطایی در تغییر وضعیت رخ داد', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // بازگرداندن وضعیت قبلی در صورت خطا
                if (statusBadge) statusBadge.innerHTML = originalContent;
                if (mobileBadge) mobileBadge.innerHTML = originalMobileContent;
                
                // نمایش اعلان خطا
                this.showNotification('خطایی در ارتباط با سرور رخ داد', 'danger');
            })
            .finally(() => {
                this.setSaveButtonLoading(false);
            });
    },
    
    // ارسال درخواست تغییر وضعیت به سرور
    sendStatusChangeRequest: function(propertyId, statusId) {
        // دریافت توکن CSRF
        const csrftoken = this.getCookie('csrftoken');
        
        // ایجاد داده‌های فرم
        const formData = new FormData();
        formData.append('status_id', statusId);
        
        // ارسال درخواست
        return fetch(`/properties/change-status/${propertyId}/`, {
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
        });
    },
    
    // به‌روزرسانی نشانگرهای وضعیت
    updateStatusBadges: function(propertyId, statusName) {
        // تعیین کلاس مناسب بر اساس نام وضعیت
        let badgeClass = this.getBadgeClassForStatus(statusName);
        
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
    },
    
    // تغییر وضعیت دکمه ذخیره به حالت بارگذاری
    setSaveButtonLoading: function(isLoading) {
        const saveBtn = document.getElementById('saveStatusChangeBtn');
        if (!saveBtn) return;
        
        const btnText = saveBtn.querySelector('.btn-text');
        const btnSpinner = saveBtn.querySelector('.btn-spinner');
        
        if (isLoading) {
            saveBtn.disabled = true;
            btnText.textContent = 'در حال ذخیره...';
            btnSpinner.classList.remove('d-none');
        } else {
            saveBtn.disabled = false;
            btnText.textContent = 'ذخیره تغییرات';
            btnSpinner.classList.add('d-none');
        }
    },
    
    // نمایش اعلان به کاربر
    showNotification: function(message, type = 'info') {
        // بررسی وجود تابع اعلان سراسری
        if (typeof showNotification === 'function') {
            showNotification(type, message);
            return;
        }
        
        // ایجاد اعلان جدید اگر تابع سراسری وجود نداشت
        const notificationId = 'status-notification-' + Date.now();
        
        // انتخاب آیکن مناسب بر اساس نوع اعلان
        let icon = 'info-circle';
        switch (type) {
            case 'success':
                icon = 'check-circle';
                break;
            case 'danger':
            case 'error':
                icon = 'exclamation-circle';
                break;
            case 'warning':
                icon = 'exclamation-triangle';
                break;
        }
        
        // ساخت HTML اعلان
        const notificationHTML = `
            <div id="${notificationId}" class="status-notification ${type}">
                <div class="notification-icon">
                    <i class="bi bi-${icon}"></i>
                </div>
                <div class="notification-message">${message}</div>
                <button type="button" class="notification-close" onclick="document.getElementById('${notificationId}').remove()">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `;
        
        // ایجاد کانتینر اعلان‌ها اگر وجود نداشت
        let container = document.getElementById('status-notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'status-notifications-container';
            document.body.appendChild(container);
        }
        
        // افزودن اعلان به کانتینر
        container.insertAdjacentHTML('beforeend', notificationHTML);
        
        // نمایش انیمیشن ظاهر شدن
        setTimeout(() => {
            const notification = document.getElementById(notificationId);
            if (notification) {
                notification.classList.add('show');
            }
        }, 10);
        
        // حذف خودکار اعلان پس از چند ثانیه
        setTimeout(() => {
            const notification = document.getElementById(notificationId);
            if (notification) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    },
    
    // دریافت کوکی CSRF
    getCookie: function(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    
    // افزودن استایل‌های CSS مورد نیاز
    addRequiredStyles: function() {
        // بررسی وجود استایل‌های قبلی
        if (document.getElementById('status-manager-styles')) return;
        
        // ایجاد عنصر استایل
        const styleElement = document.createElement('style');
        styleElement.id = 'status-manager-styles';
        
        // استایل‌های مورد نیاز
        styleElement.textContent = `
            /* استایل‌های مودال تغییر وضعیت */
            .status-modal-container {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                opacity: 0;
                transition: opacity 0.3s ease;
                padding: 1rem;
            }
            
            .status-modal-container.show {
                opacity: 1;
            }
            
            .status-modal {
                background-color: white;
                border-radius: 12px;
                width: 100%;
                max-width: 450px;
                overflow: hidden;
                transform: translateY(20px);
                transition: transform 0.3s ease;
            }
            
            .status-modal-container.show .status-modal {
                transform: translateY(0);
            }
            
            .status-modal-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 1.25rem 1.5rem;
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                color: white;
            }
            
            .status-modal-header h5 {
                margin: 0;
                font-weight: 600;
                display: flex;
                align-items: center;
                color: white;
            }
            
            .status-modal-header h5:before {
                content: "";
                display: inline-block;
                width: 22px;
                height: 22px;
                margin-left: 10px;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M0 0h24v24H0z' fill='none'/%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
                background-size: contain;
            }
            
            .status-close-btn {
                background: transparent;
                border: none;
                color: white;
                font-size: 1.5rem;
                line-height: 1;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                transition: background-color 0.2s ease;
            }
            
            .status-close-btn:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            .status-modal-body {
                padding: 1.5rem;
            }
            
            .status-property-info {
                background-color: rgba(var(--primary-rgb), 0.07);
                padding: 1rem;
                border-radius: 8px;
            }
            
            .status-property-label {
                color: var(--gray-600);
                font-size: 0.9rem;
                margin-bottom: 0.25rem;
            }
            
            .status-property-value {
                color: var(--primary-color);
                font-weight: 600;
                font-size: 1.1rem;
            }
            
            .status-options-label {
                margin-bottom: 0.75rem;
                font-weight: 500;
                color: var(--gray-700);
            }
            
            .status-options {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 0.75rem;
            }
            
            .status-option {
                padding: 0.75rem;
                border-radius: 8px;
                text-align: center;
                cursor: pointer;
                background-color: var(--gray-100);
                transition: all 0.2s ease;
                border: 2px solid transparent;
            }
            
            .status-option:hover {
                background-color: var(--gray-200);
            }
            
            .status-option.active {
                background-color: rgba(var(--primary-rgb), 0.1);
                border-color: var(--primary-color);
            }
            
            .status-badge {
                display: inline-block;
                padding: 0.5rem 0.75rem;
                border-radius: 6px;
                color: white;
                font-weight: 500;
                font-size: 0.9rem;
                width: 100%;
            }
            
            .status-modal-footer {
                padding: 1.25rem 1.5rem;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 0.75rem;
                background-color: var(--gray-100);
                border-top: 1px solid var(--gray-200);
            }
            
            .status-cancel-btn {
                padding: 0.5rem 1rem;
                border-radius: 6px;
                background-color: transparent;
                border: 1px solid var(--gray-300);
                color: var(--gray-700);
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .status-cancel-btn:hover {
                background-color: var(--gray-200);
            }
            
            .status-save-btn {
                padding: 0.5rem 1.25rem;
                border-radius: 6px;
                background-color: var(--primary-color);
                border: 1px solid var(--primary-color);
                color: white;
                font-weight: 500;
                transition: all 0.2s ease;
                position: relative;
            }
            
            .status-save-btn:hover {
                background-color: var(--primary-dark);
            }
            
            .status-save-btn:disabled {
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            /* اعلان‌ها */
            #status-notifications-container {
                position: fixed;
                top: 20px;
                left: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                align-items: center;
                pointer-events: none;
            }
            
            .status-notification {
                margin-bottom: 10px;
                padding: 1rem;
                border-radius: 8px;
                background-color: white;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                min-width: 300px;
                max-width: 450px;
                transform: translateY(-20px);
                opacity: 0;
                transition: transform 0.3s ease, opacity 0.3s ease;
                pointer-events: auto;
            }
            
            .status-notification.show {
                transform: translateY(0);
                opacity: 1;
            }
            
            .status-notification.success {
                border-right: 4px solid var(--success-color);
            }
            
            .status-notification.danger, 
            .status-notification.error {
                border-right: 4px solid var(--danger-color);
            }
            
            .status-notification.warning {
                border-right: 4px solid var(--warning-color);
            }
            
            .status-notification.info {
                border-right: 4px solid var(--info-color);
            }
            
            .notification-icon {
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                margin-right: 0.75rem;
            }
            
            .status-notification.success .notification-icon {
                color: var(--success-color);
            }
            
            .status-notification.danger .notification-icon,
            .status-notification.error .notification-icon {
                color: var(--danger-color);
            }
            
            .status-notification.warning .notification-icon {
                color: var(--warning-color);
            }
            
            .status-notification.info .notification-icon {
                color: var(--info-color);
            }
            
            .notification-message {
                flex: 1;
                font-size: 0.95rem;
            }
            
            .notification-close {
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: transparent;
                border: none;
                color: var(--gray-500);
                border-radius: 50%;
                margin-right: 0.5rem;
                transition: all 0.2s ease;
            }
            
            .notification-close:hover {
                background-color: var(--gray-200);
                color: var(--gray-700);
            }
            
            /* Media Queries */
            @media (max-width: 576px) {
                .status-modal {
                    max-width: 100%;
                }
                
                .status-options {
                    grid-template-columns: 1fr;
                }
                
                .status-notification {
                    min-width: calc(100vw - 40px);
                    max-width: calc(100vw - 40px);
                }
            }
        `;
        
        // افزودن به <head>
        document.head.appendChild(styleElement);
    }
};

// راه‌اندازی سیستم مدیریت وضعیت پس از بارگذاری صفحه
document.addEventListener('DOMContentLoaded', function() {
    StatusManager.init();
    
    // تعریف تابع جهانی برای نمایش مودال تغییر وضعیت
    window.showStatusModal = function(id, title) {
        StatusManager.showModal(id, title);
    };
});