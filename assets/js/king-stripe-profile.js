(() => {
  const form = document.querySelector('#profile-form');
  const status = document.querySelector('#profile-status');
  const key = 'ks-customer-profile';
  const read = () => {
    try { return JSON.parse(localStorage.getItem(key) || '{}') || {}; }
    catch { return {}; }
  };
  const fill = data => {
    for (const field of form.elements) {
      if (field.name && Object.hasOwn(data, field.name)) field.value = data[field.name];
    }
  };
  fill(read());
  form.addEventListener('submit', event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      localStorage.setItem(key, JSON.stringify(data));
      status.textContent = 'Saved on this device.';
    } catch {
      status.textContent = 'Could not save here. Check your browser storage settings.';
    }
  });
  document.querySelector('#clear-profile').addEventListener('click', () => {
    localStorage.removeItem(key);
    form.reset();
    form.elements.country.value = 'India';
    status.textContent = 'Profile details cleared from this device.';
  });
})();
