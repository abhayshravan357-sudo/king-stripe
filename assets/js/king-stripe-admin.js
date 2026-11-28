(() => {
  'use strict';
  const base = (window.KING_STRIPE_API || 'http://localhost:8000').replace(/\/$/, '');
  const $ = selector => document.querySelector(selector);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  let csrf = '';
  const message = (text, error = false) => {
    $('#admin-message').textContent = text;
    $('#admin-message').className = error ? 'admin-message-error' : 'admin-message-success';
  };
  async function api(path, options = {}) {
    const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(csrf && options.method && options.method !== 'GET' ? { 'X-CSRF-Token': csrf } : {}), ...options.headers };
    const response = await fetch(`${base}${path}`, { ...options, headers, credentials: 'include' });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    return data;
  }
  async function loadOrders() {
    const search = encodeURIComponent($('#order-search').value.trim());
    const status = encodeURIComponent($('#order-status').value);
    const result = await api(`/api/v1/admin/orders?limit=100&search=${search}&status_filter=${status}`);
    $('#orders-list').innerHTML = result.items.map(order => `<div class="admin-row"><strong>${esc(order.reference)}</strong><span>${esc(order.status)}</span><span>${esc(order.fulfillment_status)}</span><span>₹${(order.total_minor / 100).toLocaleString('en-IN')}</span><button type="button" data-order="${esc(order.reference)}">Details</button></div>`).join('') || '<p>No orders.</p>';
  }
  async function loadVariants() {
    const variants = await api('/api/v1/admin/variants');
    $('#variants-list').innerHTML = variants.map(v => `<article class="admin-row"><div><strong>${esc(v.product)}</strong><br><small>${esc(v.colour)} / ${esc(v.size)} · ${esc(v.sku)}</small></div><form class="admin-price-form" data-variant="${Number(v.id)}"><label>Price ₹<input name="price" type="number" min="1" step="1" value="${(v.price_minor / 100).toFixed(0)}" required></label><button type="submit">Save price</button></form><span>${v.active ? 'Active' : 'Hidden'}</span><form class="admin-inventory-form" data-variant="${Number(v.id)}"><select name="mode" aria-label="Inventory mode"><option value="limited" ${v.inventory_mode === 'limited' ? 'selected' : ''}>Limited stock</option><option value="preorder" ${v.inventory_mode === 'preorder' ? 'selected' : ''}>Preorder</option><option value="made_to_order" ${v.inventory_mode === 'made_to_order' ? 'selected' : ''}>Made to order</option><option value="unlimited" ${v.inventory_mode === 'unlimited' ? 'selected' : ''}>Unlimited</option></select><input name="quantity" type="number" min="0" aria-label="Stock quantity" value="${v.quantity_on_hand ?? ''}" placeholder="Qty"><button type="submit">Save stock</button></form><button type="button" data-active="${Number(v.id)}" data-value="${!v.active}">${v.active ? 'Disable' : 'Enable'}</button></article>`).join('');
  }
  async function loadAudit() {
    const entries = await api('/api/v1/admin/audit?limit=100');
    $('#audit-list').innerHTML = entries.map(row => `<div class="admin-row"><strong>${esc(row.action)}</strong><span>${esc(row.username)}</span><span>${esc(row.resource_type)}</span><span>${esc(row.resource_id)}</span><small>${esc(new Date(row.created_at).toLocaleString())}</small></div>`).join('') || '<p>No audit events.</p>';
  }
  $('#admin-login').addEventListener('submit', async event => {
    event.preventDefault();
    const loginForm = event.currentTarget;
    const form = new FormData(loginForm);
    try {
      const result = await api('/api/v1/admin/login', { method: 'POST', body: JSON.stringify({ username: form.get('username'), password: form.get('password') }) });
      csrf = result.csrf_token;
      $('#login-panel').hidden = true; $('#admin-panel').hidden = false;
      loginForm.reset();
      await loadOrders(); message(`Signed in as ${result.username}`);
    } catch (error) { message(error.message, true); }
  });
  $('#logout').addEventListener('click', async () => {
    try { await api('/api/v1/admin/logout', { method: 'POST' }); } catch (_) {}
    csrf = ''; $('#admin-panel').hidden = true; $('#login-panel').hidden = false; message('Signed out.');
  });
  $('#refresh-orders').addEventListener('click', () => loadOrders().catch(error => message(error.message, true)));
  $('#order-search').addEventListener('input', () => { clearTimeout(window.adminSearchTimer); window.adminSearchTimer = setTimeout(() => loadOrders().catch(error => message(error.message, true)), 250); });
  $('#order-status').addEventListener('change', () => loadOrders().catch(error => message(error.message, true)));
  document.addEventListener('click', async event => {
    const tab = event.target.closest('[data-tab]');
    if (tab) {
      document.querySelectorAll('[data-tab]').forEach(el => el.setAttribute('aria-pressed', String(el === tab)));
      ['orders', 'variants', 'audit'].forEach(name => { $(`#${name}-panel`).hidden = name !== tab.dataset.tab; });
      try { if (tab.dataset.tab === 'variants') await loadVariants(); if (tab.dataset.tab === 'audit') await loadAudit(); }
      catch (error) { message(error.message, true); }
    }
    const detailButton = event.target.closest('[data-order]');
    if (detailButton) {
      try {
        const data = await api(`/api/v1/admin/orders/${detailButton.dataset.order}`);
        const detail = $('#order-detail'); detail.hidden = false;
        detail.innerHTML = `<h2>Order ${esc(data.reference)}</h2><p>${esc(data.name)} · ${esc(data.email)}</p><p>${esc(data.shipping_address)}</p><p>Payment: ${esc(data.status)} · Fulfillment: ${esc(data.fulfillment_status)}</p><ul>${data.items.map(item => `<li>${esc(item.product)} / ${esc(item.colour)} / ${esc(item.size)} × ${Number(item.quantity)} — ₹${(item.line_total_minor / 100).toLocaleString('en-IN')}</li>`).join('')}</ul><label>Fulfillment<select id="fulfillment"><option value="unfulfilled">Unfulfilled</option><option value="processing">Processing</option><option value="fulfilled">Fulfilled</option></select></label> <button type="button" id="save-fulfillment" data-reference="${esc(data.reference)}">Update fulfillment</button>`;
        $('#fulfillment').value = data.fulfillment_status;
      } catch (error) { message(error.message, true); }
    }
    const active = event.target.closest('[data-active]');
    if (active) {
      try { await api(`/api/v1/admin/variants/${active.dataset.active}`, { method: 'PATCH', body: JSON.stringify({ active: active.dataset.value === 'true' }) }); await loadVariants(); message('Variant updated.'); }
      catch (error) { message(error.message, true); }
    }
    const save = event.target.closest('#save-fulfillment');
    if (save) {
      try { await api(`/api/v1/admin/orders/${save.dataset.reference}/fulfillment`, { method: 'PATCH', body: JSON.stringify({ status: $('#fulfillment').value }) }); await loadOrders(); message('Fulfillment updated.'); }
      catch (error) { message(error.message, true); }
    }
  });
  document.addEventListener('submit', async event => {
    const priceForm = event.target.closest('.admin-price-form');
    if (priceForm) {
      event.preventDefault();
      try {
        const price = Number(new FormData(priceForm).get('price'));
        await api(`/api/v1/admin/variants/${priceForm.dataset.variant}`, { method: 'PATCH', body: JSON.stringify({ price_minor: Math.round(price * 100) }) });
        await loadVariants(); message('Price updated.');
      } catch (error) { message(error.message, true); }
      return;
    }
    const form = event.target.closest('.admin-inventory-form');
    if (!form) return;
    event.preventDefault();
    const values = new FormData(form); const mode = values.get('mode'); const rawQuantity = values.get('quantity');
    try {
      await api(`/api/v1/admin/variants/${form.dataset.variant}/inventory`, { method: 'PUT', body: JSON.stringify({ mode, quantity_on_hand: mode === 'limited' ? Number(rawQuantity) : null }) });
      await loadVariants(); message('Inventory policy saved.');
    } catch (error) { message(error.message, true); }
  });
})();
