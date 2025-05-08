/**
 * اسکریپت مربوط به صفحه جزئیات ملک
 */

document.addEventListener('DOMContentLoaded', function() {
    // مدیریت گالری تصاویر
    initializeGallery();
    
    // اشتراک گذاری اجتماعی
    initializeSharingButtons();
    
    // نمایش موقعیت روی نقشه
    initializeMap();
});

/**
 * راه اندازی گالری تصاویر
 */
function initializeGallery() {
    const galleryThumbnails = document.querySelectorAll('.gallery-thumbnail');
    const mainImage = document.querySelector('.property-main-image img');
    const mainImageContainer = document.querySelector('.property-main-image');
    
    if (!galleryThumbnails.length || !mainImage) return;
    
    // نمایش تصویر بزرگ با کلیک روی تصاویر کوچک
    galleryThumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            const imageUrl = this.getAttribute('data-image');
            const imageTitle = this.getAttribute('data-title') || '';
            
            // انیمیشن تغییر تصویر
            mainImage.style.opacity = 0;
            setTimeout(() => {
                mainImage.src = imageUrl;
                mainImage.style.opacity = 1;
            }, 300);
            
            // فعال کردن تصویر انتخاب شده
            galleryThumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // نمایش بزرگ تصویر اصلی
    if (mainImageContainer) {
        mainImageContainer.addEventListener('click', function(e) {
            if (e.target.tagName === 'IMG') {
                openImageViewer(mainImage.src);
            }
        });
    }
    
    // نمایش بزرگ تصاویر گالری
    galleryThumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('dblclick', function() {
            const imageUrl = this.getAttribute('data-image');
            openImageViewer(imageUrl);
        });
    });
}

/**
 * باز کردن نمایش دهنده تصویر بزرگ
 */
function openImageViewer(imageUrl) {
    // ایجاد یک مودال برای نمایش تصویر
    const viewer = document.createElement('div');
    viewer.className = 'image-viewer';
    viewer.innerHTML = `
        <div class="image-viewer-backdrop"></div>
        <div class="image-viewer-content">
            <button class="image-viewer-close">&times;</button>
            <img src="${imageUrl}" alt="تصویر بزرگ" class="image-viewer-img">
        </div>
    `;
    
    document.body.appendChild(viewer);
    document.body.style.overflow = 'hidden';
    
    // اضافه کردن استایل مودال اگر وجود ندارد
    if (!document.querySelector('#image-viewer-style')) {
        const style = document.createElement('style');
        style.id = 'image-viewer-style';
        style.textContent = `
            .image-viewer {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .image-viewer-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.9);
                animation: fadeIn 0.3s;
            }
            .image-viewer-content {
                position: relative;
                max-width: 90%;
                max-height: 90%;
                z-index: 10000;
                animation: zoomIn 0.3s;
            }
            .image-viewer-img {
                max-width: 100%;
                max-height: 90vh;
                border-radius: 5px;
                box-shadow: 0 5px 30px rgba(0,0,0,0.3);
            }
            .image-viewer-close {
                position: absolute;
                top: -40px;
                right: 0;
                background: none;
                border: none;
                color: white;
                font-size: 30px;
                cursor: pointer;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes zoomIn {
                from { transform: scale(0.9); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    // رویداد بستن مودال
    const closeButton = viewer.querySelector('.image-viewer-close');
    const backdrop = viewer.querySelector('.image-viewer-backdrop');
    
    function closeViewer() {
        viewer.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(viewer);
            document.body.style.overflow = '';
        }, 300);
    }
    
    closeButton.addEventListener('click', closeViewer);
    backdrop.addEventListener('click', closeViewer);
}

/**
 * راه اندازی دکمه های اشتراک گذاری
 */
function initializeSharingButtons() {
    const shareButtons = document.querySelectorAll('[data-share]');
    
    if (!shareButtons.length) return;
    
    shareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const type = this.getAttribute('data-share');
            const title = document.querySelector('.property-title').textContent;
            const url = window.location.href;
            
            let shareUrl = '';
            
            switch(type) {
                case 'telegram':
                    shareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`;
                    break;
                case 'whatsapp':
                    shareUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(title + ' ' + url)}`;
                    break;
                case 'twitter':
                    shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(url)}`;
                    break;
                case 'copy':
                    navigator.clipboard.writeText(url).then(() => {
                        showNotification('لینک کپی شد!', 'success');
                    }).catch(err => {
                        console.error('خطا در کپی لینک:', err);
                    });
                    return;
            }
            
            if (shareUrl) {
                window.open(shareUrl, '_blank', 'width=600,height=450');
            }
        });
    });
}

/**
 * نمایش اعلان
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `property-notification ${type}`;
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
    
    // اضافه کردن استایل اعلان اگر وجود ندارد
    if (!document.querySelector('#notification-style')) {
        const style = document.createElement('style');
        style.id = 'notification-style';
        style.textContent = `
            .property-notification {
                position: fixed;
                bottom: 20px;
                left: 20px;
                background-color: white;
                color: #333;
                padding: 10px 20px;
                border-radius: 5px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                z-index: 9999;
                transform: translateY(100px);
                opacity: 0;
                transition: all 0.3s;
            }
            .property-notification.show {
                transform: translateY(0);
                opacity: 1;
            }
            .property-notification.success {
                border-right: 3px solid #28a745;
            }
            .property-notification.error {
                border-right: 3px solid #dc3545;
            }
            .property-notification.info {
                border-right: 3px solid #17a2b8;
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * راه اندازی نقشه
 */
function initializeMap() {
    const mapContainer = document.getElementById('property-map');
    
    if (!mapContainer) return;
    
    // نمایش موقعیت روی نقشه (این بخش می‌تواند با API نقشه مورد نظر پیاده‌سازی شود)
    // برای مثال اینجا یک نمونه تصویر نقشه استاتیک نمایش داده می‌شود
    mapContainer.innerHTML = `
        <div class="text-center p-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="feather feather-map text-secondary mb-2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
            <p class="text-muted">نمایش نقشه در نسخه بعدی سیستم فعال خواهد شد</p>
        </div>
    `;
}