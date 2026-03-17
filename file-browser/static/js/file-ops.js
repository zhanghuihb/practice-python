/**
 * File Browser - File Operations Module
 * 文件操作模块（复制、移动、目录选择器）
 */

// ==================== Directory Picker ====================
let dirPickerMode = null;  // 'copy' or 'move'
let dirPickerSource = null;
let dirPickerCurrentPath = '';

function showDirectoryPicker(mode, sourcePath) {
    const modal = document.getElementById('dirPickerModal');
    const title = document.getElementById('dirPickerTitle');

    dirPickerMode = mode;
    dirPickerSource = sourcePath;

    // Restore last used directory from localStorage
    const lastDir = localStorage.getItem('lastPickerDir') || '';
    dirPickerCurrentPath = lastDir;

    title.textContent = mode === 'copy' ? 'Copy to...' : 'Move to...';

    modal.classList.add('active');
    loadDirPickerContent(lastDir);

    setupDirPickerEvents();
}

async function loadDirPickerContent(path) {
    const listContainer = document.getElementById('dirPickerList');
    const breadcrumb = document.getElementById('dirPickerBreadcrumb');
    const pathInput = document.getElementById('destPathInput');

    dirPickerCurrentPath = path;
    pathInput.value = path;

    // Show loading
    listContainer.innerHTML = `
        <div class="loading" style="padding: 20px; text-align: center;">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const response = await fetch(`/api/files/subdirs?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        // Render breadcrumb
        const parts = path ? path.split('/').filter(p => p) : [];
        let breadcrumbHtml = `<span data-path="">🏠 Home</span>`;
        let currentPath = '';

        for (const part of parts) {
            currentPath += (currentPath ? '/' : '') + part;
            breadcrumbHtml += ` / <span data-path="${currentPath}">${part}</span>`;
        }

        breadcrumb.innerHTML = breadcrumbHtml;

        // Add breadcrumb click handlers
        breadcrumb.querySelectorAll('span').forEach(span => {
            span.addEventListener('click', () => {
                loadDirPickerContent(span.dataset.path);
            });
        });

        // Render directory list
        if (data.directories.length === 0) {
            listContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: var(--text-muted);">
                    No subdirectories
                </div>
            `;
        } else {
            listContainer.innerHTML = data.directories.map(dir => `
                <div class="dir-list-item" data-path="${dir.path}">
                    <i class="fas fa-folder"></i>
                    <span>${dir.name}</span>
                </div>
            `).join('');

            // Add click handlers
            listContainer.querySelectorAll('.dir-list-item').forEach(item => {
                item.addEventListener('click', () => {
                    // Toggle selection
                    listContainer.querySelectorAll('.dir-list-item').forEach(i => {
                        i.classList.remove('selected');
                    });
                    item.classList.add('selected');
                    document.getElementById('destPathInput').value = item.dataset.path;
                });

                item.addEventListener('dblclick', () => {
                    loadDirPickerContent(item.dataset.path);
                });
            });
        }
    } catch (error) {
        listContainer.innerHTML = `
            <div style="padding: 20px; text-align: center; color: var(--accent-danger);">
                Failed to load directories
            </div>
        `;
    }
}

function setupDirPickerEvents() {
    const modal = document.getElementById('dirPickerModal');
    const pathInput = document.getElementById('destPathInput');

    document.getElementById('closeDirPicker').onclick = () => {
        modal.classList.remove('active');
    };

    document.getElementById('cancelDirPicker').onclick = () => {
        modal.classList.remove('active');
    };

    modal.querySelector('.modal-overlay').onclick = () => {
        modal.classList.remove('active');
    };

    // Go to path from input
    pathInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadDirPickerContent(pathInput.value.trim());
        }
    });

    document.getElementById('confirmDirPicker').onclick = async () => {
        const destination = document.getElementById('destPathInput').value.trim();

        if (!destination && !dirPickerCurrentPath) {
            // Use root
        }

        const finalDest = destination || dirPickerCurrentPath || '';

        try {
            const endpoint = dirPickerMode === 'copy' ? '/api/files/copy' : '/api/files/move';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source: dirPickerSource,
                    destination: finalDest
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `Failed to ${dirPickerMode} file`);
            }

            modal.classList.remove('active');
            showToast(data.message, 'success');

            // Save last used directory
            localStorage.setItem('lastPickerDir', finalDest);

            // No-refresh behavior:
            if (dirPickerMode === 'move') {
                // Move: remove the file from current view
                removeFileFromState(dirPickerSource);
            }
            // Copy: just toast, no refresh needed (file stays in current dir)

        } catch (error) {
            showToast(error.message, 'error');
        }
    };
}

// ==================== Batch Operations ====================
// (可以在这里扩展批量选择和操作功能)

// ==================== Rename File ====================
// (可以在这里添加重命名功能)
