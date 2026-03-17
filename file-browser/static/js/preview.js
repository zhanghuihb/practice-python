/**
 * File Browser - Preview Module
 * 图片和文档预览模块
 */

// ==================== Image Preview ====================
let currentImageIndex = 0;

function openImagePreview(path) {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('previewImage');
    const imageInfo = document.getElementById('imageInfo');

    // Find image index in state.images
    currentImageIndex = state.images.findIndex(i => i.path === path);
    if (currentImageIndex === -1) currentImageIndex = 0;

    updateImagePreview();
    modal.classList.add('active');

    // Setup event handlers
    setupImageModalEvents();
}

function updateImagePreview() {
    if (state.images.length === 0) return;

    const image = state.images[currentImageIndex];
    const img = document.getElementById('previewImage');
    const nameSpan = document.querySelector('.image-name');
    const counterSpan = document.querySelector('.image-counter');

    img.src = `/api/preview/image/${encodeURIComponent(image.path)}`;
    nameSpan.textContent = image.name;
    counterSpan.textContent = `${currentImageIndex + 1} / ${state.images.length}`;

    // Update navigation button visibility
    document.getElementById('prevImage').style.visibility =
        currentImageIndex > 0 ? 'visible' : 'hidden';
    document.getElementById('nextImage').style.visibility =
        currentImageIndex < state.images.length - 1 ? 'visible' : 'hidden';
}

function setupImageModalEvents() {
    const modal = document.getElementById('imageModal');

    // Close button
    document.getElementById('closeImageModal').onclick = () => {
        modal.classList.remove('active');
    };

    // Click overlay to close
    modal.querySelector('.modal-overlay').onclick = () => {
        modal.classList.remove('active');
    };

    // Navigation
    document.getElementById('prevImage').onclick = () => {
        if (currentImageIndex > 0) {
            currentImageIndex--;
            updateImagePreview();
        }
    };

    document.getElementById('nextImage').onclick = () => {
        if (currentImageIndex < state.images.length - 1) {
            currentImageIndex++;
            updateImagePreview();
        }
    };

    // Keyboard navigation
    document.onkeydown = (e) => {
        if (!modal.classList.contains('active')) return;

        if (e.key === 'ArrowLeft' && currentImageIndex > 0) {
            currentImageIndex--;
            updateImagePreview();
        } else if (e.key === 'ArrowRight' && currentImageIndex < state.images.length - 1) {
            currentImageIndex++;
            updateImagePreview();
        } else if (e.key === 'Escape') {
            modal.classList.remove('active');
        }
    };

    // Action buttons
    document.getElementById('downloadImage').onclick = () => {
        const image = state.images[currentImageIndex];
        downloadFile(image.path);
    };

    document.getElementById('copyImageBtn').onclick = () => {
        const image = state.images[currentImageIndex];
        modal.classList.remove('active');
        showDirectoryPicker('copy', image.path);
    };

    document.getElementById('moveImageBtn').onclick = () => {
        const image = state.images[currentImageIndex];
        modal.classList.remove('active');
        showDirectoryPicker('move', image.path);
    };
}

// ==================== PDF Preview ====================
function openPdfPreview(path) {
    const modal = document.getElementById('docModal');
    const container = document.getElementById('docContainer');
    const title = document.getElementById('docTitle');

    const fileName = path.split('/').pop();
    title.textContent = fileName;

    // Use iframe with PDF.js or native browser PDF viewer
    container.innerHTML = `
        <iframe src="/api/preview/pdf/${encodeURIComponent(path)}" 
                style="width:100%; height:100%; border:none;">
        </iframe>
    `;

    modal.classList.add('active');
    setupDocModalEvents(path);
}

// ==================== Document Preview (DOCX/DOC) ====================
async function openDocPreview(path, type) {
    const modal = document.getElementById('docModal');
    const container = document.getElementById('docContainer');
    const title = document.getElementById('docTitle');

    const fileName = path.split('/').pop();
    title.textContent = fileName;

    // Show loading
    container.innerHTML = `
        <div class="loading" style="height: 100%; display: flex; align-items: center; justify-content: center;">
            <div class="spinner"></div>
            <span>Loading document...</span>
        </div>
    `;

    modal.classList.add('active');

    try {
        let endpoint;
        if (path.toLowerCase().endsWith('.docx')) {
            endpoint = `/api/preview/docx/${encodeURIComponent(path)}`;
        } else if (path.toLowerCase().endsWith('.doc')) {
            endpoint = `/api/preview/doc/${encodeURIComponent(path)}`;
        } else {
            throw new Error('Unsupported document format');
        }

        const response = await fetch(endpoint);

        if (!response.ok) {
            throw new Error('Failed to load document');
        }

        const html = await response.text();
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state" style="height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Cannot Preview Document</h3>
                <p>${error.message}</p>
            </div>
        `;
    }

    setupDocModalEvents(path);
}

// ==================== Text Preview ====================
async function openTextPreview(path) {
    const modal = document.getElementById('docModal');
    const container = document.getElementById('docContainer');
    const title = document.getElementById('docTitle');

    const fileName = path.split('/').pop();
    title.textContent = fileName;

    // Show loading
    container.innerHTML = `
        <div class="loading" style="height: 100%;">
            <div class="spinner"></div>
            <span>Loading...</span>
        </div>
    `;

    modal.classList.add('active');

    try {
        const response = await fetch(`/api/preview/text/${encodeURIComponent(path)}`);

        if (!response.ok) {
            throw new Error('Failed to load file');
        }

        const text = await response.text();
        container.innerHTML = `<pre>${escapeHtml(text)}</pre>`;
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state" style="height: 100%;">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Cannot Preview File</h3>
                <p>${error.message}</p>
            </div>
        `;
    }

    setupDocModalEvents(path);
}

// ==================== Document Modal Events ====================
function setupDocModalEvents(path) {
    const modal = document.getElementById('docModal');

    // Close button
    document.getElementById('closeDocModal').onclick = () => {
        modal.classList.remove('active');
    };

    // Click overlay to close
    modal.querySelector('.modal-overlay').onclick = () => {
        modal.classList.remove('active');
    };

    // Download button
    document.getElementById('downloadDoc').onclick = () => {
        downloadFile(path);
    };
}

// ==================== Utility Functions ====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
