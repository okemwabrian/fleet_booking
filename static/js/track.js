(function () {
  const container = document.querySelector('[data-tracked-code]');
  if (!container) {
    return;
  }

  const trackedCode = String(container.dataset.trackedCode || '').trim().toUpperCase();
  if (!trackedCode) {
    return;
  }

  const statusEl = document.getElementById('tracked-status');
  const locationEl = document.getElementById('tracked-location');
  const deliveryEl = document.getElementById('tracked-delivery');
  const historyEl = document.getElementById('tracking-history');

  const escapeHtml = (value) => {
    const element = document.createElement('div');
    element.textContent = value ?? '';
    return element.innerHTML;
  };

  const statusIcons = {
    RECEIVED: 'fa-box-open',
    IN_TRANSIT: 'fa-truck-fast',
    ARRIVED: 'fa-warehouse',
    DELIVERED: 'fa-circle-check',
    CANCELLED: 'fa-ban',
  };

  const formatDateTime = (value) => {
    if (!value) {
      return 'Now';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return 'Now';
    }
    return parsed.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const addHistoryItem = (parcel) => {
    if (!historyEl) return;

    const firstLine = historyEl.querySelector('p');
    if (firstLine && firstLine.textContent.includes('No timeline updates yet')) {
      firstLine.remove();
    }

    const iconClass = statusIcons[parcel.status] || 'fa-location-dot';
    const card = document.createElement('article');
    card.className = 'rounded-2xl bg-white/10 p-4';
    card.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm font-semibold text-cyan-200"><i class="fa-solid ${escapeHtml(iconClass)} mr-2"></i>${escapeHtml(parcel.status_display || parcel.status || 'Updated')}</p>
        <p class="text-xs uppercase tracking-[0.2em] text-slate-400">${escapeHtml(formatDateTime(parcel.updated_at))}</p>
      </div>
      <p class="mt-2 text-sm text-slate-300">${escapeHtml(parcel.current_location || 'No location update yet')}</p>
      <p class="mt-1 text-xs text-slate-400">Realtime update received.</p>
    `;
    historyEl.prepend(card);
  };

  const applyParcelUpdate = (parcel) => {
    if (!parcel || String(parcel.tracking_code || '').toUpperCase() !== trackedCode) {
      return;
    }

    const iconClass = statusIcons[parcel.status] || 'fa-boxes-stacked';

    if (statusEl) {
      statusEl.innerHTML = `<i class="fa-solid ${escapeHtml(iconClass)} mr-2"></i>${escapeHtml(parcel.status_display || parcel.status || 'Updated')}`;
    }
    if (locationEl) {
      locationEl.textContent = parcel.current_location || 'Pending dispatch';
    }
    if (deliveryEl) {
      deliveryEl.textContent = parcel.expected_delivery_date || 'Not set';
    }

    addHistoryItem(parcel);
  };

  window.addEventListener('fleet:parcel-realtime', (event) => {
    applyParcelUpdate(event.detail || {});
  });
})();
