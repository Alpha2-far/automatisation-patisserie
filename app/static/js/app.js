document.addEventListener('DOMContentLoaded', () => {
  // --- State Variables ---
  let categories = [];
  let activeCategorySlug = null;
  let rawUploads = [];
  let processedProducts = [];
  let selectedProcessedProduct = null;
  let statusPollInterval = null;

  // --- DOM Elements ---
  const categoriesContainer = document.getElementById('categories-container');
  const activeCategoryBadge = document.getElementById('active-category-badge');
  const uploadsPendingBadge = document.getElementById('uploads-pending-badge');
  
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const uploadProgressContainer = document.getElementById('upload-progress-container');
  const uploadProgressBar = document.getElementById('upload-progress-bar');
  const uploadPercentage = document.getElementById('upload-percentage');
  const uploadStatusText = document.getElementById('upload-status-text');

  const uploadsGrid = document.getElementById('uploads-grid');
  const uploadsCountHeader = document.getElementById('uploads-count-header');
  const processedGrid = document.getElementById('processed-grid');
  const processedCountHeader = document.getElementById('processed-count-header');

  const btnTriggerProcessHero = document.getElementById('btn-trigger-process-hero');
  const selectProcessMode = document.getElementById('select-process-mode');
  const btnExportCategoryZip = document.getElementById('btn-export-category-zip');
  const btnClearProcessedGallery = document.getElementById('btn-clear-processed-gallery');
  const btnClearRawUploads = document.getElementById('btn-clear-raw-uploads');
  const btnRefreshAll = document.getElementById('btn-refresh-all');

  // Processing Overlay Elements
  const processingOverlay = document.getElementById('processing-overlay');
  const processItemText = document.getElementById('process-item-text');
  const processProgressBar = document.getElementById('process-progress-bar');
  const processCountText = document.getElementById('process-count-text');

  // Lightbox Modal Elements
  const modalLightbox = document.getElementById('modal-lightbox');
  const btnCloseLightbox = document.getElementById('btn-close-lightbox');
  const lightboxTitle = document.getElementById('lightbox-title');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCategory = document.getElementById('lightbox-category');
  const lightboxPriceContainer = document.getElementById('lightbox-price-container');
  const lightboxPrice = document.getElementById('lightbox-price');
  const lightboxPath = document.getElementById('lightbox-path');
  const btnDeleteProcessed = document.getElementById('btn-delete-processed');

  // Category Modal Elements
  const modalCategory = document.getElementById('modal-category');
  const btnOpenCategoryModal = document.getElementById('btn-open-category-modal');
  const btnCloseCategoryModal = document.getElementById('btn-close-category-modal');
  const btnCancelCategoryModal = document.getElementById('btn-cancel-category-modal');
  const formCreateCategory = document.getElementById('form-create-category');
  const categoryNameInput = document.getElementById('category-name-input');
  const categoryPriceInput = document.getElementById('category-price-input');

  const toastContainer = document.getElementById('toast-container');

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  // --- Toast Helper ---
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-xl border shadow-lg text-xs font-semibold transition-all transform duration-300 translate-y-2 opacity-0 ${
      type === 'success' ? 'bg-emerald-600 text-white border-emerald-500' :
      type === 'error' ? 'bg-red-600 text-white border-red-500' :
      'bg-slate-900 text-white border-slate-800'
    }`;

    const iconName = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-triangle' : 'info';
    toast.innerHTML = `<i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
    
    toastContainer.appendChild(toast);
    refreshIcons();

    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
      toast.classList.add('translate-y-2', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'Ko', 'Mo', 'Go'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  // --- API: Load Categories ---
  async function loadCategories() {
    try {
      const res = await fetch('/api/categories');
      if (!res.ok) throw new Error('Erreur lors du chargement des catégories.');
      categories = await res.json();

      if (categories.length > 0) {
        if (!activeCategorySlug || !categories.find(c => c.slug === activeCategorySlug)) {
          activeCategorySlug = categories[0].slug;
        }
      } else {
        activeCategorySlug = null;
      }

      renderCategories();
      renderActiveCategoryBadge();
      updateExportLinks();
      loadUploads();
      loadProcessedProducts();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderCategories() {
    categoriesContainer.innerHTML = '';
    
    if (categories.length === 0) {
      categoriesContainer.innerHTML = `
        <button id="btn-create-first" class="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-600 text-xs font-semibold inline-flex items-center gap-1 border border-blue-200">
          <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
          <span>Créer votre première catégorie</span>
        </button>
      `;
      const btnFirst = document.getElementById('btn-create-first');
      if (btnFirst) btnFirst.addEventListener('click', openCategoryModal);
      refreshIcons();
      return;
    }

    categories.forEach(cat => {
      const isActive = cat.slug === activeCategorySlug;
      const btn = document.createElement('button');
      btn.className = `inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border shrink-0 transition-all ${
        isActive
          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
          : 'bg-white border-slate-200 text-slate-600 active:bg-slate-100'
      }`;

      const priceBadge = cat.price ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${isActive ? 'bg-emerald-500 text-white' : 'bg-emerald-100 text-emerald-700'}">${cat.price}</span>` : '';

      btn.innerHTML = `
        <span>${cat.name}</span>
        ${priceBadge}
        <span class="px-1.5 py-0.2 rounded text-[10px] font-mono ${
          isActive ? 'bg-white/20 text-white font-bold' : 'bg-slate-100 text-slate-500'
        }">${cat.upload_count || 0}</span>
      `;

      btn.addEventListener('click', () => {
        activeCategorySlug = cat.slug;
        renderCategories();
        renderActiveCategoryBadge();
        updateExportLinks();
        loadUploads();
        loadProcessedProducts();
      });

      categoriesContainer.appendChild(btn);
    });

    refreshIcons();
  }

  function renderActiveCategoryBadge() {
    const activeCat = categories.find(c => c.slug === activeCategorySlug);
    if (activeCat) {
      const priceText = activeCat.price ? ` (${activeCat.price})` : '';
      activeCategoryBadge.innerHTML = `
        <i data-lucide="tag" class="w-3.5 h-3.5 text-blue-600"></i>
        <span>Catégorie active : <strong class="text-slate-900 font-bold">${activeCat.name}</strong>${priceText}</span>
      `;
    } else {
      activeCategoryBadge.innerHTML = `
        <i data-lucide="alert-circle" class="w-3.5 h-3.5 text-amber-500"></i>
        <span>Créez une catégorie pour commencer</span>
      `;
    }
    refreshIcons();
  }

  function updateExportLinks() {
    if (btnExportCategoryZip) {
      if (activeCategorySlug) {
        btnExportCategoryZip.href = `/api/export/zip/${activeCategorySlug}`;
        btnExportCategoryZip.classList.remove('opacity-50', 'pointer-events-none');
      } else {
        btnExportCategoryZip.href = '/api/export/zip';
      }
    }
  }

  // --- API: Load Raw Uploads ---
  async function loadUploads() {
    try {
      const url = activeCategorySlug ? `/api/uploads?category_slug=${activeCategorySlug}` : '/api/uploads';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Erreur lors du chargement des captures brutes.');
      rawUploads = await res.json();
      renderRawUploads();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderRawUploads() {
    const pendingCount = rawUploads.filter(u => u.status === 'en_attente').length;
    uploadsCountHeader.textContent = rawUploads.length;
    if (uploadsPendingBadge) uploadsPendingBadge.textContent = pendingCount;
    uploadsGrid.innerHTML = '';

    if (rawUploads.length === 0) {
      uploadsGrid.className = 'col-span-full py-4 text-center';
      uploadsGrid.innerHTML = `<p class="text-xs text-slate-400">Aucune capture en attente.</p>`;
      return;
    }

    uploadsGrid.className = 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 sm:gap-4';

    rawUploads.forEach(item => {
      const card = document.createElement('div');
      card.className = 'group relative rounded-xl bg-white border border-slate-200 overflow-hidden hover:border-blue-500 shadow-sm transition-all';

      card.innerHTML = `
        <div class="relative aspect-square bg-slate-100 flex items-center justify-center overflow-hidden">
          <img src="/${item.file_path}" alt="${item.original_filename}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          <div class="absolute inset-0 bg-slate-900/40 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity flex items-end justify-end p-1.5">
            <button class="btn-delete-upload p-1.5 rounded-lg bg-red-600 text-white text-xs shadow-md" data-id="${item.id}" title="Supprimer">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>
        <div class="p-2 space-y-0.5">
          <p class="text-[11px] font-semibold text-slate-800 truncate" title="${item.original_filename}">${item.original_filename}</p>
          <div class="flex items-center justify-between text-[10px] text-slate-400">
            <span>${formatBytes(item.file_size)}</span>
            <span class="font-mono ${item.status === 'succes' ? 'text-emerald-600 font-bold' : ''}">${item.status}</span>
          </div>
        </div>
      `;

      card.querySelector('.btn-delete-upload').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteUploadItem(item.id, item.original_filename);
      });

      uploadsGrid.appendChild(card);
    });

    refreshIcons();
  }

  // --- API: Load Processed Products ---
  async function loadProcessedProducts() {
    try {
      const url = activeCategorySlug ? `/api/process/products?category_slug=${activeCategorySlug}` : '/api/process/products';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Erreur lors du chargement des produits.');
      processedProducts = await res.json();
      renderProcessedProducts();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  function renderProcessedProducts() {
    processedCountHeader.textContent = processedProducts.length;
    processedGrid.innerHTML = '';

    if (processedProducts.length === 0) {
      processedGrid.className = 'col-span-full py-6 text-center';
      processedGrid.innerHTML = `
        <p class="text-xs text-slate-400">Aucun produit rogné dans cette catégorie.</p>
      `;
      return;
    }

    processedGrid.className = 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 sm:gap-4';

    processedProducts.forEach(item => {
      const card = document.createElement('div');
      card.className = 'group relative rounded-xl bg-white border border-slate-200 overflow-hidden hover:border-blue-500 shadow-sm transition-all cursor-pointer';

      const itemPrice = item.price || item.category_price || '';
      const priceTag = itemPrice ? `<span class="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[9px]">${itemPrice}</span>` : '';

      card.innerHTML = `
        <div class="relative aspect-square bg-slate-100 flex items-center justify-center p-1 overflow-hidden">
          <img src="/${item.file_path}" alt="${item.product_name}" class="w-full h-full object-cover rounded-lg group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          
          <div class="absolute inset-0 bg-slate-900/40 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 p-2">
            <button class="btn-preview-processed p-1.5 rounded-lg bg-blue-600 text-white shadow-md" title="Agrandir">
              <i data-lucide="maximize-2" class="w-3.5 h-3.5"></i>
            </button>
            <button class="btn-delete-processed-card p-1.5 rounded-lg bg-red-600 text-white shadow-md" data-id="${item.id}" title="Supprimer">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>

        <div class="p-2 space-y-0.5">
          <p class="text-[11px] font-bold text-slate-800 truncate" title="${item.product_name}">${item.product_name}</p>
          <div class="flex items-center justify-between text-[10px] text-slate-400">
            <span class="font-medium text-blue-600 truncate">${item.category_name || item.category_slug}</span>
            ${priceTag}
          </div>
        </div>
      `;

      card.querySelector('.btn-preview-processed').addEventListener('click', (e) => {
        e.stopPropagation();
        openLightbox(item);
      });

      card.querySelector('.btn-delete-processed-card').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteProcessedItem(item.id, item.product_name);
      });

      card.addEventListener('click', () => openLightbox(item));
      processedGrid.appendChild(card);
    });

    refreshIcons();
  }

  // --- Lightbox Handlers ---
  function openLightbox(product) {
    selectedProcessedProduct = product;
    lightboxTitle.textContent = product.product_name;
    lightboxImg.src = `/${product.file_path}`;
    lightboxCategory.textContent = product.category_name || product.category_slug;
    
    const displayPrice = product.price || product.category_price || '-';
    if (lightboxPrice) lightboxPrice.textContent = displayPrice;

    lightboxPath.textContent = product.file_path;
    modalLightbox.classList.remove('hidden');
    refreshIcons();
  }

  function closeLightbox() {
    modalLightbox.classList.add('hidden');
    selectedProcessedProduct = null;
  }

  if (btnCloseLightbox) btnCloseLightbox.addEventListener('click', closeLightbox);
  if (modalLightbox) {
    modalLightbox.addEventListener('click', (e) => {
      if (e.target === modalLightbox) closeLightbox();
    });
  }

  if (btnDeleteProcessed) {
    btnDeleteProcessed.addEventListener('click', async () => {
      if (!selectedProcessedProduct) return;
      deleteProcessedItem(selectedProcessedProduct.id, selectedProcessedProduct.product_name);
      closeLightbox();
    });
  }

  // --- Delete Single Processed Item ---
  async function deleteProcessedItem(id, name) {
    if (!confirm(`Supprimer "${name}" ?`)) return;

    try {
      const res = await fetch(`/api/process/products/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Erreur lors de la suppression.');
      
      showToast(`Produit supprimé`, 'success');
      loadCategories();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // --- Clear Entire Processed Gallery ---
  if (btnClearProcessedGallery) {
    btnClearProcessedGallery.addEventListener('click', async () => {
      const catName = activeCategorySlug || 'toutes les catégories';
      if (!confirm(`Voulez-vous vider TOUS les visuels rognés de ${catName} ?`)) return;

      try {
        const url = activeCategorySlug ? `/api/process/products/clear?category_slug=${activeCategorySlug}` : '/api/process/products/clear';
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error('Erreur lors du vidage de la galerie.');

        const data = await res.json();
        showToast(data.message || 'Galerie vidée avec succès!', 'success');
        loadCategories();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // --- Clear Entire Raw Uploads Gallery ---
  if (btnClearRawUploads) {
    btnClearRawUploads.addEventListener('click', async () => {
      const catName = activeCategorySlug || 'toutes les catégories';
      if (!confirm(`Voulez-vous supprimer TOUTES les captures en attente de ${catName} ?`)) return;

      try {
        const url = activeCategorySlug ? `/api/uploads/clear?category_slug=${activeCategorySlug}` : '/api/uploads/clear';
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error('Erreur lors du vidage des captures.');

        const data = await res.json();
        showToast(data.message || 'Captures en attente effacées !', 'success');
        loadCategories();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // --- Delete Raw Upload Item ---
  async function deleteUploadItem(id, filename) {
    if (!confirm(`Voulez-vous supprimer "${filename}" ?`)) return;

    try {
      const res = await fetch(`/api/uploads/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Erreur lors de la suppression.');
      
      showToast(`Fichier supprimé`, 'success');
      loadCategories();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }

  // --- Real-time Progress Polling ---
  function startStatusPolling() {
    if (statusPollInterval) clearInterval(statusPollInterval);

    statusPollInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/process/status');
        if (!res.ok) return;
        const status = await res.json();

        if (status.is_processing) {
          const total = status.total_steps || 1;
          const current = status.current_step || 0;
          const pct = Math.round((current / total) * 100);

          processProgressBar.style.width = `${pct}%`;
          processCountText.textContent = `${current} / ${total} (${pct}%)`;
          if (status.current_filename) {
            processItemText.textContent = `${status.current_filename}`;
          }
        }
      } catch (e) {
        // Ignore polling error
      }
    }, 400);
  }

  function stopStatusPolling() {
    if (statusPollInterval) {
      clearInterval(statusPollInterval);
      statusPollInterval = null;
    }
  }

  // --- API: Trigger Automation / Image Processing ---
  async function runAutomation() {
    const selectedMode = selectProcessMode ? selectProcessMode.value : 'crop';

    if (!activeCategorySlug && categories.length === 0) {
      showToast("Veuillez d'abord créer une catégorie.", 'error');
      openCategoryModal();
      return;
    }

    processProgressBar.style.width = '0%';
    processCountText.textContent = '0 / 0';
    processItemText.textContent = 'Initialisation...';
    processingOverlay.classList.remove('hidden');

    startStatusPolling();

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category_slug: activeCategorySlug,
          mode: selectedMode
        })
      });

      const data = await res.json();
      stopStatusPolling();
      processingOverlay.classList.add('hidden');

      if (!res.ok) throw new Error(data.detail || "Erreur lors du traitement.");

      const results = data.results;
      if (results.processed_count > 0) {
        showToast(`${results.processed_count} photo(s) rognée(s) & enregistrée(s) !`, 'success');
      } else if (results.total_pending === 0) {
        showToast("Aucune capture en attente de rognage.", 'info');
      }

      if (results.failed_count > 0) {
        showToast(`${results.failed_count} fichier(s) ont échoué.`, 'error');
      }

      loadCategories();
    } catch (err) {
      stopStatusPolling();
      processingOverlay.classList.add('hidden');
      showToast(err.message, 'error');
    }
  }

  if (btnTriggerProcessHero) btnTriggerProcessHero.addEventListener('click', runAutomation);

  // --- Modal Category Listeners ---
  function openCategoryModal() {
    modalCategory.classList.remove('hidden');
    categoryNameInput.value = '';
    if (categoryPriceInput) categoryPriceInput.value = '';
    categoryNameInput.focus();
  }

  function closeCategoryModal() {
    modalCategory.classList.add('hidden');
  }

  btnOpenCategoryModal.addEventListener('click', openCategoryModal);
  btnCloseCategoryModal.addEventListener('click', closeCategoryModal);
  btnCancelCategoryModal.addEventListener('click', closeCategoryModal);

  formCreateCategory.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = categoryNameInput.value.trim();
    const price = categoryPriceInput ? categoryPriceInput.value.trim() : '';
    if (!name) return;

    try {
      const res = await fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, price })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erreur lors de la création.');

      const createdCat = data.category;
      const priceInfo = createdCat.price ? ` (${createdCat.price})` : '';
      showToast(`Catégorie "${createdCat.name}" créée${priceInfo}!`, 'success');
      closeCategoryModal();
      activeCategorySlug = createdCat.slug;
      loadCategories();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // --- Drag and Drop File Upload ---
  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dropzone-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dropzone-active');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFilesUpload(files);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFilesUpload(fileInput.files);
      fileInput.value = '';
    }
  });

  async function handleFilesUpload(files) {
    if (!activeCategorySlug) {
      showToast("Veuillez sélectionner ou créer une catégorie.", 'error');
      openCategoryModal();
      return;
    }

    const formData = new FormData();
    formData.append('category_slug', activeCategorySlug);

    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    uploadProgressContainer.classList.remove('hidden');
    uploadProgressBar.style.width = '30%';
    uploadPercentage.textContent = '30%';
    uploadStatusText.textContent = `Téléversement (${files.length})...`;

    try {
      const res = await fetch('/api/uploads', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      uploadProgressBar.style.width = '100%';
      uploadPercentage.textContent = '100%';

      if (!res.ok) throw new Error(data.detail || 'Erreur lors du téléversement.');

      if (data.uploaded_count > 0) {
        showToast(`${data.uploaded_count} capture(s) téléversée(s)!`, 'success');
      }

      setTimeout(() => {
        uploadProgressContainer.classList.add('hidden');
        uploadProgressBar.style.width = '0%';
      }, 1000);

      loadCategories();
    } catch (err) {
      uploadProgressContainer.classList.add('hidden');
      showToast(err.message, 'error');
    }
  }

  if (btnRefreshAll) {
    btnRefreshAll.addEventListener('click', () => {
      loadCategories();
      showToast('Galerie actualisée', 'info');
    });
  }

  // Initial Load
  loadCategories();
});
