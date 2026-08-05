(function () {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socketUrl = `${protocol}://${window.location.host}/ws/bookings/`;
  const toastHost = document.getElementById('realtime-toasts');
  let socket = null;
  let reconnectAttempts = 0;

  const escapeHtml = (value) => {
    const element = document.createElement('div');
    element.textContent = value ?? '';
    return element.innerHTML;
  };

  const showToast = (booking) => {
    if (!toastHost) return;
    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto glass rounded-3xl border border-cyan-400/20 bg-slate-950/90 p-4 text-sm text-slate-100 shadow-2xl';
    toast.innerHTML = `
      <p class="text-xs uppercase tracking-[0.35em] text-cyan-300">New booking</p>
      <p class="mt-2 text-base font-semibold text-white">${escapeHtml(booking.seats_booked)} seat(s) on ${escapeHtml(booking.route_origin)} to ${escapeHtml(booking.route_destination)}</p>
      <p class="mt-1 text-slate-300">${escapeHtml(booking.customer_username)} booked ${escapeHtml(booking.vehicle_label)}.</p>
    `;
    toastHost.prepend(toast);
    window.setTimeout(() => {
      toast.classList.add('opacity-0', 'transition', 'duration-300');
      window.setTimeout(() => toast.remove(), 300);
    }, 5000);
  };

  const updateDashboard = (booking) => {
    const userId = document.body.dataset.userId;
    const isStaff = document.body.dataset.isStaff === 'true';
    const currentUserId = String(userId || '');
    const bookingCustomerId = String(booking.customer_id || '');

    if (!isStaff && currentUserId !== bookingCustomerId) {
      return;
    }

    const bookingsList = document.getElementById('bookings-list');
    if (!bookingsList) return;

    const emptyState = document.getElementById('bookings-empty');
    if (emptyState) {
      emptyState.remove();
    }

    const card = document.createElement('article');
    card.className = 'booking-card rounded-3xl border border-white/10 bg-white/5 p-5';
    card.dataset.bookingId = booking.id;
    card.dataset.customerId = booking.customer_id;
    card.dataset.status = booking.status;
    const paymentProofMarkup = booking.payment_proof_url
      ? `<a class="inline-flex justify-center rounded-2xl bg-white/10 px-4 py-2 font-semibold transition hover:bg-white/15" href="${escapeHtml(booking.payment_proof_url)}" target="_blank" rel="noopener">View payment proof</a>`
      : '';
    card.innerHTML = `
      <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.3em] text-cyan-300">Booking #${escapeHtml(String(booking.id))}</p>
          <h3 class="mt-2 text-xl font-semibold text-white">${escapeHtml(booking.route_origin)} to ${escapeHtml(booking.route_destination)}</h3>
          <p class="mt-1 text-sm text-slate-400">${escapeHtml(new Date(booking.travel_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }))} - ${escapeHtml(booking.vehicle_label)} (${escapeHtml(booking.vehicle_plate)})</p>
        </div>
        <div class="flex flex-col gap-2 text-sm text-slate-100">
          <div class="booking-meta rounded-2xl bg-white/10 px-4 py-3">${escapeHtml(String(booking.seats_booked))} seat(s) | ${escapeHtml(booking.status)}</div>
          <a class="inline-flex justify-center rounded-2xl bg-cyan-400 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-300" href="${escapeHtml(booking.receipt_url)}">Download receipt</a>
          ${paymentProofMarkup}
        </div>
      </div>
      <p class="mt-4 text-sm text-slate-300">Total price: KES ${escapeHtml(booking.total_price)}</p>
    `;
    bookingsList.prepend(card);

    const incrementCounter = (id) => {
      const node = document.getElementById(id);
      if (!node) return;
      const current = parseInt(node.textContent || '0', 10);
      node.textContent = String(Number.isNaN(current) ? 1 : current + 1);
    };

    incrementCounter('count-total');
    if (booking.status === 'PENDING') incrementCounter('count-pending');
    if (booking.status === 'APPROVED') incrementCounter('count-approved');
    if (booking.status === 'COMPLETED') incrementCounter('count-completed');
  };

  const updateDashboardStatus = (booking) => {
    const userId = document.body.dataset.userId;
    const isStaff = document.body.dataset.isStaff === 'true';
    const currentUserId = String(userId || '');
    const bookingCustomerId = String(booking.customer_id || '');

    if (!isStaff && currentUserId !== bookingCustomerId) {
      return;
    }

    const card = document.querySelector(`.booking-card[data-booking-id="${CSS.escape(String(booking.id))}"]`);
    if (!card) {
      return;
    }

    const oldStatus = card.dataset.status || '';
    const newStatus = booking.status || oldStatus;
    if (oldStatus === newStatus) {
      return;
    }

    const decrementCounter = (id) => {
      const node = document.getElementById(id);
      if (!node) return;
      const current = parseInt(node.textContent || '0', 10);
      node.textContent = String(Math.max(Number.isNaN(current) ? 0 : current - 1, 0));
    };

    const incrementCounter = (id) => {
      const node = document.getElementById(id);
      if (!node) return;
      const current = parseInt(node.textContent || '0', 10);
      node.textContent = String(Number.isNaN(current) ? 1 : current + 1);
    };

    const statusCounterMap = {
      PENDING: 'count-pending',
      APPROVED: 'count-approved',
      COMPLETED: 'count-completed',
    };

    if (statusCounterMap[oldStatus]) decrementCounter(statusCounterMap[oldStatus]);
    if (statusCounterMap[newStatus]) incrementCounter(statusCounterMap[newStatus]);

    card.dataset.status = newStatus;
    const meta = card.querySelector('.booking-meta');
    if (meta) {
      const seatsLabel = `${escapeHtml(String(booking.seats_booked || ''))} seat(s)`;
      meta.innerHTML = `${seatsLabel} | ${escapeHtml(newStatus)}`;
    }

    if (!card.querySelector('.status-live-badge')) {
      const badge = document.createElement('p');
      badge.className = 'status-live-badge mt-3 text-xs uppercase tracking-[0.25em] text-cyan-300';
      badge.textContent = 'Status updated live';
      card.appendChild(badge);
    }
  };

  const updateSearchResults = (booking) => {
    const currentView = document.body.dataset.view;
    if (currentView !== 'search') return;

    const selectors = [
      `.search-option[data-route-id="${CSS.escape(String(booking.route_id))}"][data-vehicle-id="${CSS.escape(String(booking.vehicle_id))}"][data-travel-date="${CSS.escape(String(booking.travel_date))}"]`,
    ];

    const option = document.querySelector(selectors.join(','));
    if (!option) return;

    const seatCount = option.querySelector('.seat-count');
    if (!seatCount) return;

    const seatNumbers = Array.isArray(booking.seat_numbers) ? booking.seat_numbers : [];
    seatNumbers.forEach((seatNumber) => {
      const seatButton = option.querySelector(`.seat-button[data-seat-number="${CSS.escape(String(seatNumber))}"]`);
      if (!seatButton) return;

      seatButton.disabled = true;
      seatButton.classList.remove(
        'bg-slate-200',
        'text-slate-900',
        'hover:bg-slate-300',
        'bg-orange-500',
        'text-white',
        'hover:bg-orange-400',
      );
      seatButton.classList.add('bg-slate-700', 'text-slate-300', 'cursor-not-allowed');
    });

    const currentText = seatCount.textContent || '';
    const remainingMatch = currentText.match(/(\d+)/);
    const currentRemaining = remainingMatch ? parseInt(remainingMatch[1], 10) : 0;
    const nextRemaining = Math.max(currentRemaining - Number(booking.seats_booked || 0), 0);
    seatCount.textContent = `${nextRemaining} seats left`;

    const seatNumbersInput = option.querySelector('.seat-numbers-input');
    const selectedLabel = option.querySelector('.selected-seats-label');
    const totalLabel = option.querySelector('.booking-total-price');
    if (seatNumbersInput && selectedLabel && totalLabel) {
      let selectedSeats = [];
      try {
        const parsed = JSON.parse(seatNumbersInput.value || '[]');
        selectedSeats = Array.isArray(parsed) ? parsed : [];
      } catch (error) {
        selectedSeats = [];
      }

      const updatedSelection = selectedSeats.filter((seat) => !seatNumbers.includes(Number(seat))).sort((a, b) => a - b);
      seatNumbersInput.value = JSON.stringify(updatedSelection);
      selectedLabel.textContent = updatedSelection.length ? updatedSelection.join(', ') : 'None';
      const basePrice = Number(option.dataset.basePrice || 0);
      totalLabel.textContent = `KES ${(basePrice * updatedSelection.length).toFixed(2)}`;
    }

    if (nextRemaining === 0) {
      const button = option.querySelector('.continue-booking-button');
      if (button) {
        button.disabled = true;
        button.classList.add('opacity-50', 'cursor-not-allowed');
        button.textContent = 'Sold out';
      }
    }
  };

  const handleMessage = (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch (error) {
      return;
    }

    if (!payload) {
      return;
    }

    if ((payload.type === 'parcel.created' || payload.type === 'parcel.updated') && payload.parcel) {
      window.dispatchEvent(new CustomEvent('fleet:parcel-realtime', { detail: payload.parcel }));
      return;
    }

    if (!payload.booking) {
      return;
    }

    if (payload.type === 'booking.created') {
      showToast(payload.booking);
      updateDashboard(payload.booking);
      updateSearchResults(payload.booking);
      return;
    }

    if (payload.type === 'booking.updated') {
      updateDashboardStatus(payload.booking);
    }
  };

  const connectSocket = () => {
    socket = new WebSocket(socketUrl);

    socket.addEventListener('open', () => {
      reconnectAttempts = 0;
    });

    socket.addEventListener('message', handleMessage);

    socket.addEventListener('close', () => {
      const delay = Math.min(3000 * (reconnectAttempts + 1), 12000);
      reconnectAttempts += 1;
      window.setTimeout(connectSocket, delay);
    });

    socket.addEventListener('error', () => {
      socket.close();
    });
  };

  connectSocket();
})();