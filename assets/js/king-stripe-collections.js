(() => {
  'use strict';

  const products = [
    { id: 1, name: 'Crowned Tiger', type: 'Pullover', price: 3499, colourways: ['Bone', 'Midnight', 'Ember'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' },
    { id: 2, name: 'Midnight King', type: 'Zip', price: 3999, colourways: ['Midnight', 'Ash'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' },
    { id: 3, name: 'Rock Throne', type: 'Oversized', price: 4299, colourways: ['Bone', 'Ash'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' },
    { id: 4, name: 'Ember Stripe', type: 'Pullover', price: 3599, colourways: ['Ember', 'Midnight'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' },
    { id: 5, name: 'Ash Prowl', type: 'Zip', price: 3899, colourways: ['Ash', 'Bone'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' },
    { id: 6, name: 'Night Orbit', type: 'Oversized', price: 4499, colourways: ['Midnight', 'Ember'], sizes: ['S', 'M', 'L', 'XL', 'XXL'], collection: '001' }
  ];
  const collections = [
    { id: '001', slug: 'tiger-black', animal: 'Tiger', colour: 'Black', title: 'Tiger × Black', tagline: 'Power in every stripe.', description: 'The current King Stripe collection. Tiger artwork, a black-led identity and six hoodie silhouettes to explore.', status: 'Available', featured: true, artwork: 'assets/tiger_crowned.svg', heroImage: 'assets/tiger_crowned.svg', campaignImages: [], productIds: products.map(p => p.id), accent: '#191916' },
    { id: '002', slug: 'wolf-grey', animal: 'Wolf', colour: 'Grey', tagline: 'Independence · Loyalty · Strength', status: 'Concept example', accent: '#868782', campaignImages: [], productIds: [] },
    { id: '003', slug: 'panther-red', animal: 'Panther', colour: 'Red', tagline: 'Stealth · Confidence · Intensity', status: 'Concept example', accent: '#621d22', campaignImages: [], productIds: [] },
    { id: '004', slug: 'eagle-blue', animal: 'Eagle', colour: 'Blue', tagline: 'Vision · Freedom · Ambition', status: 'Concept example', accent: '#293b50', campaignImages: [], productIds: [] }
  ];
  const colourValues = { Bone: '#ded9ca', Midnight: '#11110f', Ember: '#a5a4a0', Ash: '#777770' };
  const money = value => `₹${value.toLocaleString('en-IN')}`;
  const $ = (query, root = document) => root.querySelector(query);
  const $$ = (query, root = document) => [...root.querySelectorAll(query)];
  const productById = id => products.find(product => product.id === Number(id));
  let bag = safeRead('ks-redesign-bag', []);
  let saved = safeRead('ks-redesign-saved', []);
  let selectedFilter = 'all';
  let selectedProduct = null;
  let selectedColour = '';
  let selectedSize = '';
  const cardColours = {};
  let toastTimer;

  function safeRead(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key) || 'null') || fallback; } catch { return fallback; }
  }
  function safeWrite(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Storage may be unavailable. */ }
  }
  function shirtSvg(product, colour, back = false) {
    const fill = colourValues[colour] || '#ded9ca';
    const key = `garment-${product.id}-${colour.toLowerCase()}-${back ? 'back' : 'front'}-${Math.random().toString(36).slice(2, 7)}`;
    const body = 'M82 43 Q101 51 120 48 Q140 51 158 43 L184 55 221 130 193 145 175 111 179 232 Q120 244 61 232 L65 111 47 145 19 130 56 55Z';
    const hood = back
      ? '<path d="M84 47C78 29 87 10 105 6Q121 2 137 8C153 14 161 30 155 48L143 61Q140 39 120 34Q99 39 96 61Z" fill="url(#cloth)" stroke="#11110f" stroke-width="2.4"/><path d="M98 39Q120 31 142 39" fill="none" stroke="#fff" stroke-opacity=".26" stroke-width="1.5"/>'
      : '<path d="M84 48C77 31 82 11 101 6Q120 0 139 7C158 14 163 32 154 49L142 62Q140 38 120 34Q100 38 97 62Z" fill="url(#cloth)" stroke="#11110f" stroke-width="2.4"/><path d="M98 39Q120 31 142 39" fill="none" stroke="#11110f" stroke-opacity=".65" stroke-width="2"/><path d="M105 43L102 91M135 43L138 91" stroke="#4a4943" stroke-opacity=".8" stroke-width="2"/><path d="M102 91l-3 5m39-5 3 5" stroke="#11110f" stroke-width="2" stroke-linecap="round"/>';
    const pocket = back ? '' : product.type === 'Zip'
      ? '<path d="M69 150L94 160M146 160l25-10" stroke="#11110f" stroke-width="1.5"/><path d="M70 150l-7 20m108-20 7 20" stroke="#fff" stroke-opacity=".28" stroke-width="1"/>'
      : '<path d="M79 151Q120 159 161 151L151 186Q120 197 89 186Z" fill="url(#pocket)" stroke="#11110f" stroke-width="1.7"/><path d="M88 158Q120 165 152 158" fill="none" stroke="#fff" stroke-opacity=".32" stroke-width="1.3"/><path d="M120 165v18" stroke="#11110f" stroke-opacity=".3" stroke-width="1"/>';
    const closure = product.type === 'Zip'
      ? '<path d="M120 46V231" stroke="#11110f" stroke-width="2"/><path d="M118 53h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4m-4 5h4" stroke="#fff" stroke-opacity=".45" stroke-width="1"/><path d="M117 49h6v6h-6z" fill="#aaa79e" stroke="#11110f" stroke-width="1"/>'
      : '';
    const seams = back
      ? '<path d="M71 65Q120 82 169 65M66 220Q120 229 174 220" fill="none" stroke="#fff" stroke-opacity=".27" stroke-width="1.5"/><path d="M68 74Q120 90 172 74" fill="none" stroke="#11110f" stroke-opacity=".22" stroke-width="1"/>'
      : '<path d="M71 62Q120 76 169 62M66 222Q120 230 174 222" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="1.5"/><path d="M70 70Q120 83 170 70" fill="none" stroke="#11110f" stroke-opacity=".22" stroke-width="1"/>';
    const hoodMarkup = hood.replaceAll('url(#cloth)', `url(#${key}-cloth)`);
    return `<svg class="hoodie ${back ? 'back-view' : 'front-view'}" viewBox="0 0 240 250" role="img" aria-label="${back ? 'Back' : 'Front'} view of ${product.name} hoodie in ${colour}"><defs><linearGradient id="${key}-cloth" x1="0" y1="0" x2="1" y2=".9"><stop offset="0" stop-color="${fill}"/><stop offset=".48" stop-color="${fill}"/><stop offset="1" stop-color="#77756e" stop-opacity=".24"/></linearGradient><linearGradient id="${key}-pocket" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#11110f" stop-opacity=".1"/></linearGradient></defs><ellipse cx="120" cy="239" rx="85" ry="5" fill="#11110f" opacity=".1"/>${hoodMarkup}<path d="${body}" fill="url(#${key}-cloth)" stroke="#11110f" stroke-width="2.8" stroke-linejoin="round"/><path d="M56 57L21 130 47 143 65 109M184 57l36 73-27 13-18-34" fill="none" stroke="#fff" stroke-opacity=".27" stroke-width="1.6" stroke-linejoin="round"/><path d="M63 111L60 222M177 111l3 111" fill="none" stroke="#11110f" stroke-opacity=".3" stroke-width="1.4"/>${seams}${pocket.replaceAll('url(#pocket)', `url(#${key}-pocket)`)}${closure}<path d="M64 213Q120 222 176 213L179 232Q120 244 61 232Z" fill="#11110f" fill-opacity=".08" stroke="#11110f" stroke-width="1.5"/><path d="M67 218Q120 227 173 218M68 224Q120 233 172 224" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1"/><path d="M39 132l17 6v22q-13 5-23-4l-4-16ZM201 132l-17 6v22q13 5 23-4l4-16Z" fill="url(#${key}-cloth)" stroke="#11110f" stroke-width="2"/><path d="M35 145q10 6 20 2m-32-1 26 9m155-10q-10 6-20 2m32-1-26 9" fill="none" stroke="#fff" stroke-opacity=".38" stroke-width="1"/>${product.type === 'Oversized' ? '<path d="M78 56l-4 161m88-161 4 161" fill="none" stroke="#11110f" stroke-opacity=".11" stroke-width="2"/>' : ''}${back ? '<path d="M120 57v14" stroke="#11110f" stroke-opacity=".24" stroke-width="1.5"/>' : ''}</svg>`;
  }
  function renderCollections() {
    $('#collection-grid').innerHTML = collections.map(collection => {
      const actual = collection.status === 'Available';
      const art = actual
        ? `<img src="${collection.artwork}" alt="" aria-hidden="true">`
        : `<span aria-hidden="true">${collection.animal.slice(0, 2).toUpperCase()}</span>`;
      const inner = `<div class="collection-card-top"><span>${actual ? `COLLECTION ${collection.id}` : `SYSTEM EXAMPLE ${collection.id}`}</span><span>${actual ? 'AVAILABLE ↗' : 'NOT RELEASED'}</span></div><div class="collection-card-art">${art}</div><div class="collection-card-bottom"><div><small>${collection.animal.toUpperCase()} / ${collection.colour.toUpperCase()}${actual ? '' : ' · CONCEPT'}</small><strong>${collection.animal}<b>×</b>${collection.colour}</strong><span class="collection-tagline">${collection.tagline}</span></div><span aria-hidden="true">${actual ? '↗' : '·'}</span></div>`;
      return actual
        ? `<a class="collection-card" data-collection="${collection.id}" style="--collection:${collection.accent}" href="?collection=${collection.slug}#collection-page" aria-label="Explore Collection ${collection.id}: ${collection.title}">${inner}</a>`
        : `<article class="collection-card is-concept" data-concept="${collection.animal.toLowerCase()}" style="--collection:${collection.accent}" aria-label="${collection.title}, concept example not released">${inner}</article>`;
    }).join('');
  }
  function renderFeaturedCollection() {
    const featured = collections.find(collection => collection.featured && collection.status === 'Available');
    if (!featured) return;
    $('[data-featured-label]').textContent = `FEATURED COLLECTION ${featured.id}`;
    $('[data-featured-number]').textContent = `${featured.id} / ${String(collections.length).padStart(2, '0')}`;
    $('[data-featured-art]').src = featured.heroImage || featured.artwork;
    $('[data-featured-art]').alt = `${featured.animal} artwork for Collection ${featured.id}`;
    $('[data-featured-title]').innerHTML = `${featured.animal.toUpperCase()} <b>×</b> ${featured.colour.toUpperCase()}`;
    $('[data-featured-tagline]').textContent = featured.tagline.toUpperCase();
  }
  function productCard(product) {
    const colour = cardColours[product.id] || product.colourways[0];
    const isSaved = saved.includes(product.id);
    const edition = String(products.findIndex(item => item.id === product.id) + 1).padStart(2, '0');
    const darkGarment = colour === 'Midnight';
    return `<article class="product-card" data-product="${product.id}"><div class="product-visual"><span class="product-tag">COLLECTION 001 <i>— ${edition}</i></span><button class="product-wish" type="button" aria-label="${isSaved ? 'Remove from' : 'Add to'} saved pieces: ${product.name}" aria-pressed="${isSaved}" data-wish="${product.id}">${isSaved ? '♥' : '♡'}</button>${shirtSvg(product, colour)}<img class="garment-print front-print ${darkGarment ? 'print-light' : ''}" src="assets/tiger_scarred.svg" alt="" aria-hidden="true">${shirtSvg(product, colour, true)}<img class="garment-print back-print ${darkGarment ? 'print-light' : ''}" src="assets/tiger_scarred.svg" alt="" aria-hidden="true"><button class="product-view-label" type="button" data-flip aria-pressed="false" aria-label="Show back of ${product.name}">FRONT <span>↔</span> BACK</button></div><div class="product-meta"><div class="product-title-row"><h3>${product.name}</h3><span class="product-price">${money(product.price)}</span></div><p>${product.type} hoodie <span>·</span> Tiger × Black</p><div class="product-card-bottom"><div class="product-swatches" role="group" aria-label="Choose garment colour for ${product.name}">${product.colourways.map(c => `<button class="product-swatch ${c === colour ? 'selected' : ''}" type="button" data-card-colour="${c}" data-card-product="${product.id}" title="${c}" aria-label="Show ${c} ${product.name}" aria-pressed="${c === colour}" style="--swatch:${colourValues[c]};${c === 'Midnight' ? 'border-color:#bbb' : ''}"></button>`).join('')}</div><span class="swatch-name">${colour}</span><button class="quick-view-btn" type="button" data-open-product="${product.id}">View details <span>↗</span></button></div></div></article>`;
  }
  function renderProducts(target = '#product-grid', filter = selectedFilter) {
    const root = $(target);
    if (!root) return;
    let shown = products.filter(p => filter === 'all' || p.type === filter);
    if (target === '#collection-products') {
      const collectionId = $('#collection-page')?.dataset.collection;
      const currentCollection = collections.find(collection => collection.id === collectionId);
      shown = products.filter(p => currentCollection?.productIds.includes(p.id));
    }
    if (target === '#product-grid') {
      const sort = $('#product-sort')?.value;
      if (sort === 'low') shown.sort((a, b) => a.price - b.price);
      if (sort === 'high') shown.sort((a, b) => b.price - a.price);
    }
    root.innerHTML = shown.map(productCard).join('') || '<p class="empty-products">No products in this selection yet.</p>';
  }
  function updateCounts() {
    $$('[data-bag-count]').forEach(el => el.textContent = bag.reduce((total, item) => total + item.quantity, 0));
    $$('[data-wish-count]').forEach(el => el.textContent = saved.length);
  }
  function notify(message) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2100);
  }
  function openProduct(id) {
    selectedProduct = productById(id);
    if (!selectedProduct) return;
    selectedColour = selectedProduct.colourways[0];
    selectedSize = '';
    renderProductDialog();
    $('#product-dialog').showModal();
  }
  function renderProductDialog() {
    const p = selectedProduct;
    const parentCollection = collections.find(collection => collection.id === p.collection);
    $('#product-dialog').innerHTML = `<div class="product-dialog-layout"><div class="dialog-visual">${shirtSvg(p, selectedColour)}${shirtSvg(p, selectedColour, true)}</div><div class="dialog-info"><button class="close-dialog" data-close="product-dialog" aria-label="Close product details">×</button><p class="eyebrow">Collection ${p.collection} / ${parentCollection?.title || 'King Stripe'}</p><h2 id="dialog-title">${p.name}</h2><div class="dialog-price">${money(p.price)}</div><p class="dialog-description">${p.type} silhouette. Select an available garment colour and size to add this piece to your bag.</p><span class="dialog-label">Garment colour / ${selectedColour}</span><div class="variant-row">${p.colourways.map(c => `<button class="variant-choice ${c === selectedColour ? 'selected' : ''}" type="button" data-colour="${c}">${c}</button>`).join('')}</div><span class="dialog-label">Select size</span><div class="size-row">${p.sizes.map(size => `<button class="size-choice ${size === selectedSize ? 'selected' : ''}" type="button" data-size="${size}">${size}</button>`).join('')}</div><button class="dialog-add" type="button" data-add="${p.id}">${selectedSize ? 'Add to bag' : 'Choose a size'}</button><p class="dialog-description">Collection colour describes the artwork identity. Garment colourways are selected separately.</p></div></div>`;
  }
  function addToBag(id, colour, size) {
    if (!size) { notify('Choose a size first'); return; }
    const existing = bag.find(item => item.id === Number(id) && item.colour === colour && item.size === size);
    if (existing) existing.quantity += 1;
    else bag.push({ id: Number(id), colour, size, quantity: 1 });
    safeWrite('ks-redesign-bag', bag);
    updateCounts();
    notify('Added to your bag');
    closeDialog('product-dialog');
    renderBag();
  }
  function renderBag() {
    const content = $('#bag-content');
    const footer = $('#bag-footer');
    if (!bag.length) {
      content.innerHTML = '<p class="bag-empty">Your bag is empty. Discover the current collection to find your piece.</p>';
      footer.innerHTML = '<a class="checkout-button" href="index.html#shop" data-close="bag-dialog">Explore the collection</a>';
      return;
    }
    content.innerHTML = bag.map((item, index) => {
      const p = productById(item.id);
      if (!p) return '';
      return `<article class="bag-line"><div class="bag-line-art">${shirtSvg(p, item.colour)}</div><div><h3>${p.name}</h3><p>${item.colour} / ${item.size}</p><div class="bag-qty"><button type="button" aria-label="Decrease quantity" data-quantity="${index}" data-step="-1">−</button><span>${item.quantity}</span><button type="button" aria-label="Increase quantity" data-quantity="${index}" data-step="1">+</button><button type="button" data-remove="${index}">Remove</button></div></div><span class="bag-line-price">${money(p.price * item.quantity)}</span></article>`;
    }).join('');
    const total = bag.reduce((sum, item) => sum + productById(item.id).price * item.quantity, 0);
    footer.innerHTML = `<div class="bag-total"><span>Subtotal</span><span>${money(total)}</span></div><p class="checkout-note">Preview checkout only. No payment will be taken.</p><button class="checkout-button" type="button" data-checkout>Continue to demo checkout</button>`;
  }
  function renderWishlist() {
    const root = $('#wish-content');
    if (!saved.length) { root.innerHTML = '<p class="bag-empty">No saved pieces yet. Use the heart on a product to keep it here.</p>'; return; }
    root.innerHTML = saved.map(id => {
      const p = productById(id);
      return p ? `<div class="wish-row"><div><strong>${p.name}</strong><br><small>${money(p.price)} / Collection 001</small></div><button type="button" data-open-product="${p.id}">View piece ↗</button></div>` : '';
    }).join('');
  }
  function toggleSaved(id) {
    const numericId = Number(id);
    saved = saved.includes(numericId) ? saved.filter(value => value !== numericId) : [...saved, numericId];
    safeWrite('ks-redesign-saved', saved);
    updateCounts();
    renderProducts();
    const collectionProducts = $('#collection-products');
    if (collectionProducts) renderProducts('#collection-products');
    renderWishlist();
  }
  function closeDialog(id) { const dialog = document.getElementById(id); if (dialog?.open) dialog.close(); }
  function collectionPage(collection) {
    const section = $('#collection-page');
    if (!collection || collection.status !== 'Available') return false;
    const homeSections = $$('#main > section:not(#collection-page)');
    homeSections.forEach(el => { el.hidden = true; });
    $('.ticker').hidden = true;
    section.hidden = false;
    section.dataset.collection = collection.id;
    section.innerHTML = `<a class="collection-back" href="index.html#collections">← All collections</a><div class="collection-page-head"><div class="collection-page-hero"><img src="${collection.artwork}" alt="${collection.animal} artwork for Collection ${collection.id}"></div><div><p class="eyebrow">King Stripe / Collection ${collection.id}</p><h1 id="collection-page-title">${collection.animal}<em>× ${collection.colour}</em></h1><p class="collection-tagline">${collection.tagline}</p><p>${collection.description}</p><a class="button button-light" href="#collection-products">Explore the drop <span>↓</span></a></div></div><div class="collection-story"><div><p class="eyebrow">The identity / 001</p><h2>${collection.animal.toUpperCase()}<br>AFTER DARK.</h2><p>Collection colour shapes the atmosphere. The animal gives this release its own voice. Garment colourways stay specific to each piece.</p></div><div class="collection-artwork"><img src="assets/tiger_scarred.svg" alt="Alternate tiger artwork for Collection ${collection.id}"><span>ARTWORK DETAIL / 001</span></div></div><div class="section-topline"><span>COLLECTION ${collection.id} / PRODUCTS</span><span>${collection.productIds.length} PIECES</span></div><div class="collection-page-products"><div class="product-grid" id="collection-products"></div></div><div class="collection-campaign"><span class="eyebrow">CAMPAIGN / ${collection.id}</span><p>Campaign photography for this collection will appear here when approved images are available.</p></div><div class="collection-garment"><p class="eyebrow">THE CLOTHING</p><h2>ART HAS A HOME.<br><em>THE GARMENT IS IT.</em></h2><p>Explore the available silhouettes, garment colours and sizes in the pieces above.</p></div><a class="collection-back" href="index.html#collections">← Return to all collections</a>`;
    document.title = `Collection ${collection.id}: ${collection.title} — King Stripe`;
    document.body.classList.add('is-collection');
    renderProducts('#collection-products');
    return true;
  }

  renderFeaturedCollection();
  renderCollections();
  renderProducts();
  renderBag();
  renderWishlist();
  updateCounts();
  const route = new URLSearchParams(location.search).get('collection');
  if (route) {
    const collection = collections.find(item => item.slug === route);
    if (!collectionPage(collection)) notify('That collection is not available yet');
    else $$('.main-nav a, #mobile-nav a, .footer-bottom a').forEach(link => {
      const section = link.getAttribute('href')?.split('#')[1];
      if (section) link.href = `index.html#${section}`;
    });
  }

  $$('.filter').forEach(button => button.addEventListener('click', () => {
    selectedFilter = button.dataset.filter;
    $$('.filter').forEach(item => { item.classList.toggle('active', item === button); item.setAttribute('aria-pressed', item === button); });
    renderProducts();
  }));
  $('#product-sort').addEventListener('change', () => renderProducts());
  document.addEventListener('click', event => {
    const close = event.target.closest('[data-close]');
    if (close) { event.preventDefault(); closeDialog(close.dataset.close); return; }
    const wish = event.target.closest('[data-wish]');
    if (wish) { event.stopPropagation(); toggleSaved(wish.dataset.wish); return; }
    const cardColour = event.target.closest('[data-card-colour]');
    if (cardColour) {
      event.stopPropagation();
      cardColours[Number(cardColour.dataset.cardProduct)] = cardColour.dataset.cardColour;
      renderProducts();
      const collectionProducts = $('#collection-products');
      if (collectionProducts) renderProducts('#collection-products');
      return;
    }
    const flip = event.target.closest('[data-flip]');
    if (flip) {
      event.stopPropagation();
      const card = flip.closest('.product-card');
      const back = card.dataset.view !== 'back';
      card.dataset.view = back ? 'back' : 'front';
      flip.setAttribute('aria-pressed', String(back));
      flip.setAttribute('aria-label', `${back ? 'Show front' : 'Show back'} of ${productById(card.dataset.product).name}`);
      flip.innerHTML = `${back ? 'BACK' : 'FRONT'} <span>↔</span> SHOW ${back ? 'FRONT' : 'BACK'}`;
      return;
    }
    const card = event.target.closest('.product-card');
    if (card && !event.target.closest('.product-swatch')) { openProduct(card.dataset.product); return; }
    const colour = event.target.closest('[data-colour]');
    if (colour) { selectedColour = colour.dataset.colour; renderProductDialog(); return; }
    const size = event.target.closest('[data-size]');
    if (size) { selectedSize = size.dataset.size; renderProductDialog(); return; }
    const add = event.target.closest('[data-add]');
    if (add) { addToBag(add.dataset.add, selectedColour, selectedSize); return; }
    const bagTrigger = event.target.closest('.bag-trigger');
    if (bagTrigger) { renderBag(); $('#bag-dialog').showModal(); return; }
    if (event.target.closest('[data-checkout]')) { closeDialog('bag-dialog'); $('#checkout-dialog').showModal(); return; }
    const wishTrigger = event.target.closest('.wishlist-trigger');
    if (wishTrigger) { renderWishlist(); $('#wish-dialog').showModal(); return; }
    const openProductButton = event.target.closest('[data-open-product]');
    if (openProductButton) { closeDialog('wish-dialog'); openProduct(openProductButton.dataset.openProduct); return; }
    const remove = event.target.closest('[data-remove]');
    if (remove) { bag.splice(Number(remove.dataset.remove), 1); safeWrite('ks-redesign-bag', bag); renderBag(); updateCounts(); return; }
    const quantity = event.target.closest('[data-quantity]');
    if (quantity) { const index = Number(quantity.dataset.quantity); bag[index].quantity += Number(quantity.dataset.step); if (bag[index].quantity < 1) bag.splice(index, 1); safeWrite('ks-redesign-bag', bag); renderBag(); updateCounts(); return; }
  });
  document.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('.product-visual')) { event.preventDefault(); openProduct(event.target.closest('.product-card').dataset.product); }
  });
  document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  }));
  $('#checkout-form').addEventListener('submit', event => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    $('#checkout-dialog').close();
    bag = [];
    safeWrite('ks-redesign-bag', bag);
    renderBag();
    updateCounts();
    notify('Demo order reviewed — no order was placed');
  });
  const menuButton = $('.menu-trigger');
  const mobileNav = $('#mobile-nav');
  menuButton.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!open));
    mobileNav.hidden = open;
    menuButton.setAttribute('aria-label', open ? 'Open menu' : 'Close menu');
  });
  $$('#mobile-nav a').forEach(link => link.addEventListener('click', () => {
    menuButton.setAttribute('aria-expanded', 'false');
    mobileNav.hidden = true;
    menuButton.setAttribute('aria-label', 'Open menu');
  }));
})();
