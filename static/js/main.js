/**
 * اسکریپت‌های عمومی سیستم مدیریت املاک هیرو
 * بهینه‌سازی شده برای دستگاه‌های مختلف و عملکرد بهتر
 * نسخه 2.0.0
 */

// تنظیمات عمومی
const HIRO = {
    settings: {
        autoDetectDevice: true,       // تشخیص خودکار نوع دستگاه
        enableAnimations: true,       // فعال‌سازی انیمیشن‌ها
        persianNumbers: true,         // تبدیل اعداد به فارسی
        autoCloseAlerts: true,        // بستن خودکار هشدارها
        alertCloseTime: 5000,         // زمان بسته شدن هشدارها (میلی‌ثانیه)
        lazyLoadImages: true,         // بارگذاری تنبل تصاویر
        enableDarkMode: false,        // فعال‌سازی حالت تاریک
        debugMode: false,             // حالت دیباگ
    },
    
    device: {
        isMobile: false,              // آیا دستگاه موبایل است
        isTablet: false,              // آیا دستگاه تبلت است
        isDesktop: false,             // آیا دستگاه دسکتاپ است
        isSmallScreen: false,         // آیا صفحه کوچک است
        orientation: 'portrait',      // جهت نمایش
        browser: '',                  // نوع مرورگر
        os: '',                       // سیستم عامل
    },
    
    // متدهای سیستم
    init: function() {
        // تشخیص دستگاه
        if (this.settings.autoDetectDevice) {
            this.detectDevice();
        }
        
        // تنظیم کلاس‌های HTML بر اساس دستگاه
        this.applyDeviceClasses();
        
        // فعال‌سازی ویژگی‌های مختلف
        this.initializeFeatures();
        
        // گزارش راه‌اندازی در حالت دیباگ
        if (this.settings.debugMode) {
            console.log('HIRO System Initialized', {
                device: this.device,
                settings: this.settings
            });
        }
        
        // بررسی ارتفاع و پدینگ‌های صفحه
        this.adjustPageLayout();
        
        // متد لیسنر تغییر اندازه پنجره
        window.addEventListener('resize', () => {
            this.detectDevice();
            this.applyDeviceClasses();
            this.adjustPageLayout();
        });
        
        // ذخیره ترجیحات کاربر
        this.saveUserPreferences();
    },
    
    // تشخیص نوع دستگاه و ویژگی‌های آن
    detectDevice: function() {
        const ua = navigator.userAgent.toLowerCase();
        const width = window.innerWidth;
        
        // بررسی نوع دستگاه
        this.device.isMobile = /android|webos|iphone|ipod|blackberry|iemobile|opera mini/i.test(ua);
        this.device.isTablet = this.device.isMobile && (width >= 768 || /ipad/i.test(ua));
        this.device.isDesktop = !this.device.isMobile && !this.device.isTablet;
        this.device.isSmallScreen = width < 992;
        
        // تشخیص جهت نمایش
        this.device.orientation = width > window.innerHeight ? 'landscape' : 'portrait';
        
        // تشخیص مرورگر و سیستم عامل
        if (ua.indexOf('edge') > -1) this.device.browser = 'edge';
        else if (ua.indexOf('firefox') > -1) this.device.browser = 'firefox';
        else if (ua.indexOf('chrome') > -1) this.device.browser = 'chrome';
        else if (ua.indexOf('safari') > -1) this.device.browser = 'safari';
        else if (ua.indexOf('opera') > -1) this.device.browser = 'opera';
        else if (ua.indexOf('msie') > -1 || ua.indexOf('trident') > -1) this.device.browser = 'ie';
        
        if (ua.indexOf('windows') > -1) this.device.os = 'windows';
        else if (ua.indexOf('mac') > -1) this.device.os = 'mac';
        else if (ua.indexOf('linux') > -1) this.device.os = 'linux';
        else if (ua.indexOf('android') > -1) this.device.os = 'android';
        else if (ua.indexOf('iphone') > -1 || ua.indexOf('ipad') > -1) this.device.os = 'ios';
    },
    
    // اعمال کلاس‌های مرتبط با دستگاه به تگ body
    applyDeviceClasses: function() {
        const body = document.body;
        
        // حذف تمام کلاس‌های قبلی دستگاه
        body.classList.remove('mobile-device', 'tablet-device', 'desktop-device', 'small-screen', 'landscape', 'portrait');
        
        // اضافه کردن کلاس‌های جدید
        if (this.device.isMobile) body.classList.add('mobile-device');
        if (this.device.isTablet) body.classList.add('tablet-device');
        if (this.device.isDesktop) body.classList.add('desktop-device');
        if (this.device.isSmallScreen) body.classList.add('small-screen');
        body.classList.add(this.device.orientation);
        
        // اضافه کردن کلاس مرورگر و سیستم عامل
        if (this.device.browser) body.classList.add(`browser-${this.device.browser}`);
        if (this.device.os) body.classList.add(`os-${this.device.os}`);
        
        // تنظیم اندازه فونت بر اساس عرض صفحه
        const baseFontSize = Math.min(16, Math.max(14, window.innerWidth / 80));
        document.documentElement.style.fontSize = baseFontSize + 'px';
    },
    
    // تنظیم فاصله‌ها و ارتفاع‌های صفحه
    adjustPageLayout: function() {
        // تنظیم پدینگ برای محتوای اصلی در حالت موبایل
        const mainContent = document.querySelector('main');
        const mobileNavbar = document.querySelector('.mobile-navbar');
        
        if (mainContent && mobileNavbar && this.device.isMobile) {
            const navbarHeight = mobileNavbar.offsetHeight;
            mainContent.style.paddingTop = (navbarHeight + 16) + 'px';
        } else if (mainContent) {
            mainContent.style.paddingTop = '';
        }
        
        // تنظیم ارتفاع محتوای اصلی حداقل برابر با ارتفاع صفحه منهای هدر و فوتر
        const header = document.querySelector('header');
        const footer = document.querySelector('footer');
        
        if (mainContent && header && footer) {
            const minHeight = window.innerHeight - (header.offsetHeight + footer.offsetHeight);
            mainContent.style.minHeight = minHeight + 'px';
        }
    },
    
    // راه‌اندازی ویژگی‌های مختلف
    initializeFeatures: function() {
        // فعال‌سازی تولتیپ‌ها
        initTooltips();
        
        // فعال‌سازی المان‌های select2 در صورت وجود
        initSelect2();
        
        // فرمت کردن اعداد فارسی
        if (this.settings.persianNumbers) {
            formatPersianNumbers();
        }
        
        // نمایش پیش‌نمایش تصاویر در هنگام آپلود
        setupImagePreview();
        
        // اضافه کردن مدیریت بسته شدن خودکار alert‌ها
        if (this.settings.autoCloseAlerts) {
            setupAlertDismiss();
        }
        
        // فعال‌سازی Lazy Loading تصاویر
        if (this.settings.lazyLoadImages) {
            this.enableLazyLoading();
        }
        
        // مدیریت منوی موبایل
        setupMobileMenu();
        
        // مدیریت فیلترهای جستجو در صفحه جستجوی پیشرفته
        setupFilterToggle();
        
        // نمایش تاییدیه قبل از حذف
        setupDeleteConfirmation();
        
        // نمایش/مخفی کردن دکمه بازگشت به بالا
        this.setupBackToTop();
        
        // بهینه‌سازی کلیک‌ها برای دستگاه‌های لمسی
        this.optimizeTouchInteractions();
    },
    
    // فعال‌سازی بارگذاری تنبل برای تصاویر
    enableLazyLoading: function() {
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    },
    
    // راه‌اندازی دکمه بازگشت به بالا
    setupBackToTop: function() {
        const backToTopBtn = document.getElementById('backToTop');
        if (backToTopBtn) {
            window.addEventListener('scroll', function() {
                if (window.pageYOffset > 300) {
                    backToTopBtn.classList.remove('d-none');
                    if (HIRO.settings.enableAnimations) {
                        backToTopBtn.classList.add('animate__animated', 'animate__fadeIn');
                    }
                } else {
                    backToTopBtn.classList.add('d-none');
                    if (HIRO.settings.enableAnimations) {
                        backToTopBtn.classList.remove('animate__animated', 'animate__fadeIn');
                    }
                }
            });
        }
    },
    
    // بهینه‌سازی تعاملات لمسی
    optimizeTouchInteractions: function() {
        if (this.device.isMobile || this.device.isTablet) {
            // اضافه کردن کلاس touch به body
            document.body.classList.add('touch-device');
            
            // بهبود عملکرد هاور برای دستگاه‌های لمسی
            document.querySelectorAll('.hover-effect').forEach(element => {
                element.addEventListener('touchstart', function() {
                    this.classList.add('hover-active');
                });
                
                element.addEventListener('touchend', function() {
                    this.classList.remove('hover-active');
                });
            });
        }
    },
    
    // ذخیره ترجیحات کاربر در localStorage
    saveUserPreferences: function() {
        // ذخیره ترجیحات در localStorage
        const userPrefs = {
            darkMode: this.settings.enableDarkMode,
            lastVisit: new Date().toISOString()
        };
        
        try {
            localStorage.setItem('hiro_user_prefs', JSON.stringify(userPrefs));
        } catch (e) {
            if (this.settings.debugMode) {
                console.warn('Unable to save user preferences to localStorage', e);
            }
        }
    }
};

// اجرای کد پس از لود شدن صفحه
document.addEventListener('DOMContentLoaded', function() {
    // راه‌اندازی سیستم
    HIRO.init();
    
    // سایر کدهای اختصاصی صفحه...
    
    // فعال‌سازی انیمیشن‌ها اگر تنظیمات آن فعال باشد
    if (HIRO.settings.enableAnimations) {
        document.querySelectorAll('.animate-on-scroll').forEach(element => {
            new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate__animated', 'animate__fadeInUp');
                    }
                });
            }, { threshold: 0.1 }).observe(element);
        });
    }
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
    try {
        // بررسی وجود jQuery و کتابخانه select2
        if (typeof($) !== 'undefined' && $ !== null && typeof($.fn) !== 'undefined' && typeof($.fn.select2) !== 'undefined') {
            $('.select2').select2({
                dir: 'rtl',
                language: 'fa'
            });
        } else {
            console.log('کتابخانه Select2 یا jQuery بارگذاری نشده است.');
        }
    } catch (e) {
        console.log('خطا در راه‌اندازی Select2:', e);
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
