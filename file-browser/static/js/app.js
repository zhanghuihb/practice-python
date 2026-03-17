/**
 * File Browser - Main Application JavaScript
 * 文件浏览器主应用脚本
 */

// ==================== State ====================
const state = {
    currentPath: '',
    files: [],
    images: [],
    selectedFile: null,
    viewMode: localStorage.getItem('viewMode') || 'grid',  // 'grid' or 'list'
    iconSize: localStorage.getItem('iconSize') || 'large',  // 'large' or 'small'
    theme: localStorage.getItem('theme') || 'dark',
    // Pagination
    currentPage: 1,
    pageSize: parseInt(localStorage.getItem('pageSize')) || 20,
    totalItems: 0
};

// ==================== DOM Elements ====================
const elements = {
    fileGrid: document.getElementById('fileGrid'),
    breadcrumb: document.getElementById('breadcrumb'),
    pathInput: document.getElementById('pathInput'),
    searchInput: document.getElementById('searchInput'),
    statsInfo: document.getElementById('statsInfo'),
    directoryTree: document.getElementById('directoryTree'),
    contextMenu: document.getElementById('contextMenu'),
    toastContainer: document.getElementById('toastContainer'),
    dropZone: document.getElementById('dropZone'),
    fileUpload: document.getElementById('fileUpload'),

    // Pagination
    paginationBar: document.getElementById('paginationBar'),
    paginationPages: document.getElementById('paginationPages'),
    pageSizeSelect: document.getElementById('pageSizeSelect'),
    paginationInfo: document.getElementById('paginationInfo'),

    // Buttons
    toggleSidebar: document.getElementById('toggleSidebar'),
    toggleTheme: document.getElementById('toggleTheme'),
    uploadBtn: document.getElementById('uploadBtn'),
    newFolderBtn: document.getElementById('newFolderBtn'),
    refreshBtn: document.getElementById('refreshBtn'),
    viewToggleBtn: document.getElementById('viewToggleBtn'),
    iconSizeBtn: document.getElementById('iconSizeBtn'),
    goPath: document.getElementById('goPath')
};

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initViewMode();
    initIconSize();
    initPagination();
    initEventListeners();
    loadDirectory('');
});

function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function initViewMode() {
    elements.fileGrid.classList.toggle('list-view', state.viewMode === 'list');
    const icon = elements.viewToggleBtn.querySelector('i');
    icon.className = state.viewMode === 'grid' ? 'fas fa-th-large' : 'fas fa-list';
}

function initIconSize() {
    applyIconSize();
    updateIconSizeBtn();
}

function applyIconSize() {
    elements.fileGrid.classList.remove('icon-small', 'icon-large');
    elements.fileGrid.classList.add(`icon-${state.iconSize}`);
}

function updateIconSizeBtn() {
    const icon = elements.iconSizeBtn.querySelector('i');
    icon.className = state.iconSize === 'large' ? 'fas fa-expand' : 'fas fa-compress';
    elements.iconSizeBtn.title = state.iconSize === 'large' ? 'Switch to Small Icons' : 'Switch to Large Icons';
}

function initPagination() {
    elements.pageSizeSelect.value = state.pageSize;
}

function updateThemeIcon() {
    const icon = elements.toggleTheme.querySelector('i');
    icon.className = state.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function initEventListeners() {
    // Sidebar toggle
    elements.toggleSidebar.addEventListener('click', () => {
        document.querySelector('.sidebar').classList.toggle('collapsed');
    });

    // Theme toggle
    elements.toggleTheme.addEventListener('click', () => {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', state.theme);
        document.documentElement.setAttribute('data-theme', state.theme);
        updateThemeIcon();
    });

    // View toggle
    elements.viewToggleBtn.addEventListener('click', () => {
        state.viewMode = state.viewMode === 'grid' ? 'list' : 'grid';
        localStorage.setItem('viewMode', state.viewMode);
        elements.fileGrid.classList.toggle('list-view', state.viewMode === 'list');
        const icon = elements.viewToggleBtn.querySelector('i');
        icon.className = state.viewMode === 'grid' ? 'fas fa-th-large' : 'fas fa-list';
    });

    // Icon size toggle
    elements.iconSizeBtn.addEventListener('click', () => {
        state.iconSize = state.iconSize === 'large' ? 'small' : 'large';
        localStorage.setItem('iconSize', state.iconSize);
        applyIconSize();
        updateIconSizeBtn();
    });

    // Page size change
    elements.pageSizeSelect.addEventListener('change', (e) => {
        state.pageSize = parseInt(e.target.value);
        state.currentPage = 1;
        localStorage.setItem('pageSize', state.pageSize);
        renderCurrentPage();
    });

    // Refresh
    elements.refreshBtn.addEventListener('click', () => {
        loadDirectory(state.currentPath);
    });

    // Path input
    elements.goPath.addEventListener('click', () => {
        const path = elements.pathInput.value.trim();
        loadDirectory(path);
    });

    elements.pathInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const path = elements.pathInput.value.trim();
            loadDirectory(path);
        }
    });

    // Search
    let searchTimeout;
    elements.searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            filterFiles(e.target.value);
        }, 300);
    });

    // Upload button
    elements.uploadBtn.addEventListener('click', () => {
        elements.fileUpload.click();
    });

    elements.fileUpload.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFiles(e.target.files);
        }
    });

    // New folder button
    elements.newFolderBtn.addEventListener('click', () => {
        showNewFolderModal();
    });

    // Context menu
    document.addEventListener('click', () => {
        hideContextMenu();
    });

    document.addEventListener('contextmenu', (e) => {
        if (!e.target.closest('.file-item')) {
            hideContextMenu();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close modals
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });

    // Drag and drop
    initDragDrop();
}

// ==================== Directory Loading ====================
async function loadDirectory(path) {
    state.currentPath = path;
    state.currentPage = 1;
    elements.pathInput.value = path;

    // Show loading
    elements.fileGrid.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <span>Loading...</span>
        </div>
    `;

    try {
        const response = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load directory');
        }

        state.files = data.items;
        state.images = data.images;
        state.totalItems = data.items.length;

        renderBreadcrumb(data.breadcrumbs);
        renderCurrentPage();
        renderStats(data.stats);

        // Update directory tree (only for root level)
        if (!path) {
            loadDirectoryTree('');
        }
    } catch (error) {
        showToast(error.message, 'error');
        elements.fileGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error Loading Directory</h3>
                <p>${error.message}</p>
            </div>
        `;
        elements.paginationBar.style.display = 'none';
    }
}

async function loadDirectoryTree(path) {
    try {
        const response = await fetch(`/api/files/subdirs?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        elements.directoryTree.innerHTML = data.directories.map(dir => `
            <div class="tree-item" data-path="${dir.path}">
                <i class="fas fa-folder"></i>
                <span>${dir.name}</span>
            </div>
        `).join('');

        // Add click handlers
        elements.directoryTree.querySelectorAll('.tree-item').forEach(item => {
            item.addEventListener('click', () => {
                loadDirectory(item.dataset.path);
            });
        });
    } catch (error) {
        console.error('Failed to load directory tree:', error);
    }
}

// ==================== Pagination ====================
function getPagedFiles(files) {
    const start = (state.currentPage - 1) * state.pageSize;
    const end = start + state.pageSize;
    return files.slice(start, end);
}

function renderCurrentPage() {
    const displayFiles = state._filteredFiles || state.files;
    const pagedFiles = getPagedFiles(displayFiles);
    renderFileGrid(pagedFiles);
    renderPagination(displayFiles.length);
}

function renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / state.pageSize);

    if (totalPages <= 1) {
        elements.paginationBar.style.display = 'none';
        return;
    }

    elements.paginationBar.style.display = 'flex';

    // Page info
    const start = (state.currentPage - 1) * state.pageSize + 1;
    const end = Math.min(state.currentPage * state.pageSize, totalItems);
    elements.paginationInfo.textContent = `${start}-${end} / ${totalItems}`;

    // Page buttons
    let pagesHtml = '';

    // Previous button
    pagesHtml += `<button ${state.currentPage <= 1 ? 'disabled' : ''} data-page="${state.currentPage - 1}"><i class="fas fa-chevron-left"></i></button>`;

    // Page numbers with ellipsis
    const pages = generatePageNumbers(state.currentPage, totalPages);
    for (const p of pages) {
        if (p === '...') {
            pagesHtml += `<span class="page-ellipsis">...</span>`;
        } else {
            pagesHtml += `<button class="${p === state.currentPage ? 'active' : ''}" data-page="${p}">${p}</button>`;
        }
    }

    // Next button
    pagesHtml += `<button ${state.currentPage >= totalPages ? 'disabled' : ''} data-page="${state.currentPage + 1}"><i class="fas fa-chevron-right"></i></button>`;

    elements.paginationPages.innerHTML = pagesHtml;

    // Add click handlers
    elements.paginationPages.querySelectorAll('button:not(:disabled)').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page >= 1 && page <= totalPages) {
                state.currentPage = page;
                renderCurrentPage();
                // Scroll to top of file container
                document.querySelector('.file-container').scrollTop = 0;
            }
        });
    });
}

function generatePageNumbers(current, total) {
    if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1);
    }

    const pages = [];
    pages.push(1);

    if (current > 3) {
        pages.push('...');
    }

    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);

    for (let i = start; i <= end; i++) {
        pages.push(i);
    }

    if (current < total - 2) {
        pages.push('...');
    }

    pages.push(total);

    return pages;
}

// ==================== Rendering ====================
function renderBreadcrumb(breadcrumbs) {
    elements.breadcrumb.innerHTML = breadcrumbs.map((crumb, index) => {
        const isLast = index === breadcrumbs.length - 1;
        const separator = isLast ? '' : '<span class="breadcrumb-separator">/</span>';
        const className = isLast ? 'breadcrumb-item active' : 'breadcrumb-item';

        return `
            <a href="#" class="${className}" data-path="${crumb.path}">${crumb.name}</a>
            ${separator}
        `;
    }).join('');

    // Add click handlers
    elements.breadcrumb.querySelectorAll('.breadcrumb-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            loadDirectory(item.dataset.path);
        });
    });
}

function renderFileGrid(files) {
    if (files.length === 0) {
        elements.fileGrid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>Empty Directory</h3>
                <p>No files or folders in this directory</p>
            </div>
        `;
        return;
    }

    elements.fileGrid.innerHTML = files.map(file => {
        const iconHtml = file.is_image
            ? `<img src="/api/preview/thumb/${encodeURIComponent(file.path)}" class="file-thumb" alt="${file.name}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
            : '';

        const iconFallback = `<div class="file-icon ${file.type}" ${file.is_image ? 'style="display:none"' : ''}>
            <i class="fas fa-${file.icon}"></i>
        </div>`;

        return `
            <div class="file-item" 
                 data-path="${file.path}" 
                 data-type="${file.type}"
                 data-name="${file.name}"
                 data-is-dir="${file.is_dir}"
                 data-is-image="${file.is_image}"
                 data-is-previewable="${file.is_previewable}">
                ${iconHtml}
                ${iconFallback}
                <span class="file-name">${file.name}</span>
                <span class="file-meta">${file.size_human || ''}</span>
            </div>
        `;
    }).join('');

    // Preserve icon size and view mode classes
    applyIconSize();

    // Add event listeners
    elements.fileGrid.querySelectorAll('.file-item').forEach(item => {
        // Double click to open
        item.addEventListener('dblclick', () => {
            handleFileOpen(item);
        });

        // Single click to select
        item.addEventListener('click', (e) => {
            if (e.detail === 1) {
                selectFile(item);
            }
        });

        // Right click for context menu
        item.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            selectFile(item);
            showContextMenu(e.clientX, e.clientY, item);
        });
    });
}

function renderStats(stats) {
    elements.statsInfo.textContent =
        `${stats.total_items} items (${stats.dir_count} folders, ${stats.file_count} files) • ${stats.total_size_human}`;
}

function updateStatsFromState() {
    const dirs = state.files.filter(f => f.is_dir);
    const files = state.files.filter(f => !f.is_dir);
    const totalSize = files.reduce((sum, f) => sum + (f.size || 0), 0);
    elements.statsInfo.textContent =
        `${state.files.length} items (${dirs.length} folders, ${files.length} files) • ${formatSize(totalSize)}`;
}

function formatSize(size) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    for (const unit of units) {
        if (size < 1024) {
            return unit === 'B' ? `${size} ${unit}` : `${size.toFixed(1)} ${unit}`;
        }
        size /= 1024;
    }
    return `${size.toFixed(1)} PB`;
}

// ==================== File Operations ====================
function selectFile(item) {
    // Remove previous selection
    elements.fileGrid.querySelectorAll('.file-item.selected').forEach(el => {
        el.classList.remove('selected');
    });

    item.classList.add('selected');
    state.selectedFile = {
        path: item.dataset.path,
        type: item.dataset.type,
        name: item.dataset.name,
        isDir: item.dataset.isDir === 'true',
        isImage: item.dataset.isImage === 'true',
        isPreviewable: item.dataset.isPreviewable === 'true'
    };
}

function handleFileOpen(item) {
    const isDir = item.dataset.isDir === 'true';
    const isImage = item.dataset.isImage === 'true';
    const type = item.dataset.type;
    const path = item.dataset.path;

    if (isDir) {
        loadDirectory(path);
    } else if (isImage) {
        openImagePreview(path);
    } else if (type === 'pdf') {
        openPdfPreview(path);
    } else if (type === 'document' || item.dataset.path.endsWith('.doc')) {
        openDocPreview(path, type);
    } else if (type === 'text') {
        openTextPreview(path);
    } else {
        // Download other files
        downloadFile(path);
    }
}

function filterFiles(query) {
    if (!query) {
        state._filteredFiles = null;
        state.currentPage = 1;
        renderCurrentPage();
        return;
    }

    state._filteredFiles = state.files.filter(file =>
        file.name.toLowerCase().includes(query.toLowerCase())
    );
    state.currentPage = 1;
    renderCurrentPage();
}

// Remove a file from state (used for no-refresh deletion/move)
function removeFileFromState(path) {
    state.files = state.files.filter(f => f.path !== path);
    state.images = state.images.filter(f => f.path !== path);
    state.totalItems = state.files.length;

    // Reset filtered files if active
    if (state._filteredFiles) {
        state._filteredFiles = state._filteredFiles.filter(f => f.path !== path);
    }

    // Check if current page is now empty
    const displayFiles = state._filteredFiles || state.files;
    const totalPages = Math.ceil(displayFiles.length / state.pageSize);
    if (state.currentPage > totalPages && totalPages > 0) {
        state.currentPage = totalPages;
    }

    renderCurrentPage();
    updateStatsFromState();
}

// ==================== Context Menu ====================
function showContextMenu(x, y, item) {
    const menu = elements.contextMenu;

    // Position menu
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.classList.add('active');

    // Adjust if off screen
    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        menu.style.left = `${x - rect.width}px`;
    }
    if (rect.bottom > window.innerHeight) {
        menu.style.top = `${y - rect.height}px`;
    }

    // Add action handlers
    menu.querySelectorAll('li[data-action]').forEach(li => {
        li.onclick = () => {
            handleContextAction(li.dataset.action);
            hideContextMenu();
        };
    });
}

function hideContextMenu() {
    elements.contextMenu.classList.remove('active');
}

function handleContextAction(action) {
    if (!state.selectedFile) return;

    switch (action) {
        case 'preview':
            const item = document.querySelector(`.file-item[data-path="${state.selectedFile.path}"]`);
            if (item) handleFileOpen(item);
            break;
        case 'download':
            downloadFile(state.selectedFile.path);
            break;
        case 'copy':
            showDirectoryPicker('copy', state.selectedFile.path);
            break;
        case 'move':
            showDirectoryPicker('move', state.selectedFile.path);
            break;
        case 'trash':
            moveToTrash(state.selectedFile.path);
            break;
    }
}

// ==================== Modals ====================
function closeAllModals() {
    document.querySelectorAll('.modal.active').forEach(modal => {
        modal.classList.remove('active');
    });
}

function showNewFolderModal() {
    const modal = document.getElementById('newFolderModal');
    const input = document.getElementById('newFolderName');

    modal.classList.add('active');
    input.value = '';
    input.focus();

    // Event handlers
    document.getElementById('closeNewFolder').onclick = () => modal.classList.remove('active');
    document.getElementById('cancelNewFolder').onclick = () => modal.classList.remove('active');
    document.getElementById('confirmNewFolder').onclick = () => createNewFolder();

    input.onkeypress = (e) => {
        if (e.key === 'Enter') createNewFolder();
    };
}

async function createNewFolder() {
    const name = document.getElementById('newFolderName').value.trim();
    if (!name) {
        showToast('Please enter a folder name', 'error');
        return;
    }

    try {
        const response = await fetch('/api/files/mkdir', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                parent: state.currentPath,
                name: name
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to create folder');
        }

        document.getElementById('newFolderModal').classList.remove('active');
        showToast(`Created folder: ${name}`, 'success');
        loadDirectory(state.currentPath);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// ==================== Drag and Drop ====================
function initDragDrop() {
    const dropZone = elements.dropZone;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        document.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    document.addEventListener('dragenter', () => {
        dropZone.classList.add('active');
    });

    dropZone.addEventListener('dragleave', (e) => {
        if (e.target === dropZone) {
            dropZone.classList.remove('active');
        }
    });

    dropZone.addEventListener('drop', (e) => {
        dropZone.classList.remove('active');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFiles(files);
        }
    });
}

async function uploadFiles(files) {
    const formData = new FormData();
    formData.append('path', state.currentPath);

    for (const file of files) {
        formData.append('files', file);
    }

    showToast(`Uploading ${files.length} file(s)...`, 'info');

    try {
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        const successCount = data.uploads.filter(u => u.success).length;
        const failCount = data.uploads.filter(u => !u.success).length;

        if (failCount > 0) {
            showToast(`Uploaded ${successCount} files, ${failCount} failed`, 'error');
        } else {
            showToast(`Uploaded ${successCount} file(s) successfully`, 'success');
        }

        loadDirectory(state.currentPath);
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
    }

    // Reset file input
    elements.fileUpload.value = '';
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'info') {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;

    elements.toastContainer.appendChild(toast);

    // Auto remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== Utility Functions ====================
function downloadFile(path) {
    const link = document.createElement('a');
    link.href = `/api/preview/download/${encodeURIComponent(path)}`;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function moveToTrash(path) {
    if (!confirm('Move this file to trash?')) return;

    try {
        const response = await fetch(`/api/files/trash?path=${encodeURIComponent(path)}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to move to trash');
        }

        showToast(data.message, 'success');
        // No page refresh — just remove from state
        removeFileFromState(path);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Navigation links in sidebar
document.querySelectorAll('.nav-item[data-path]').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        loadDirectory(item.dataset.path);
    });
});
