// DriftGuard Alert Management JS

let activeAlertId = null;
let activeActionType = null; // 'acknowledge' or 'resolve'

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

function promptAcknowledge(alertId) {
  activeAlertId = alertId;
  activeActionType = 'acknowledge';
  document.getElementById('modal-title').innerText = `Acknowledge Alert #${alertId}`;
  document.getElementById('modal-label').innerText = 'Operator Name';
  document.getElementById('modal-input').value = 'ops-team';
  document.getElementById('action-modal').classList.remove('hidden');
}

function promptResolve(alertId) {
  activeAlertId = alertId;
  activeActionType = 'resolve';
  document.getElementById('modal-title').innerText = `Resolve Alert #${alertId}`;
  document.getElementById('modal-label').innerText = 'Resolution Note / Action Taken';
  document.getElementById('modal-input').value = 'Inspected GPU and replaced thermal paste';
  document.getElementById('action-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('action-modal').classList.add('hidden');
  activeAlertId = null;
  activeActionType = null;
}

document.addEventListener('DOMContentLoaded', () => {
  const submitBtn = document.getElementById('modal-submit-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      const val = document.getElementById('modal-input').value.trim();
      if (!activeAlertId || !activeActionType) return;

      const endpoint = activeActionType === 'acknowledge'
        ? `/api/v1/alerts/${activeAlertId}/acknowledge/`
        : `/api/v1/alerts/${activeAlertId}/resolve/`;

      const payload = activeActionType === 'acknowledge'
        ? { acknowledged_by: val || 'ops-team' }
        : { resolution_note: val || 'Resolved by operator' };

      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        closeModal();
        // Update table row in-place
        const badgeEl = document.getElementById(`status-badge-${data.id}`);
        if (badgeEl) {
          badgeEl.innerText = data.status;
          if (data.status === 'acknowledged') {
            badgeEl.className = 'px-2 py-0.5 rounded text-2xs font-semibold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20';
          } else if (data.status === 'resolved') {
            badgeEl.className = 'px-2 py-0.5 rounded text-2xs font-semibold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
          }
        }
      })
      .catch(err => alert('Error completing action: ' + err));
    });
  }

  // Filter application handler
  const filterBtn = document.getElementById('btn-apply-filters');
  if (filterBtn) {
    filterBtn.addEventListener('click', () => {
      const status = document.getElementById('filter-status').value;
      const severity = document.getElementById('filter-severity').value;
      const node = document.getElementById('filter-node').value;

      let url = `/api/v1/alerts/?`;
      if (status) url += `status=${status}&`;
      if (severity) url += `severity=${severity}&`;
      if (node) url += `node=${node}&`;

      fetch(url)
        .then(res => res.json())
        .then(data => {
          const tbody = document.getElementById('alerts-table-body');
          if (!tbody) return;
          const alertsList = data.results || data;

          if (alertsList.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-12 text-slate-500">No alerts match the selected criteria.</td></tr>`;
            return;
          }

          tbody.innerHTML = alertsList.map(a => `
            <tr id="alert-row-${a.id}" class="hover:bg-slate-750 transition-colors">
              <td class="px-5 py-4">
                <span class="px-2.5 py-1 rounded text-2xs font-bold uppercase tracking-wider ${a.severity === 'critical' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}">
                  ${a.severity}
                </span>
              </td>
              <td class="px-5 py-4 font-mono font-bold">
                <a href="/nodes/${a.node_id}/" class="text-blue-400 hover:underline">${a.node_id}</a>
              </td>
              <td class="px-5 py-4 text-slate-300 max-w-lg">${a.message}</td>
              <td class="px-5 py-4 text-slate-400 font-mono">${new Date(a.triggered_at).toLocaleString()}</td>
              <td class="px-5 py-4">
                <span id="status-badge-${a.id}" class="px-2 py-0.5 rounded text-2xs font-semibold uppercase ${a.status === 'open' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : (a.status === 'acknowledged' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20')}">
                  ${a.status}
                </span>
              </td>
              <td class="px-5 py-4 text-right space-x-2">
                ${a.status === 'open' ? `<button onclick="promptAcknowledge(${a.id})" class="px-2.5 py-1 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 border border-amber-500/30 rounded text-2xs font-semibold">Acknowledge</button>` : ''}
                ${a.status !== 'resolved' ? `<button onclick="promptResolve(${a.id})" class="px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 border border-emerald-500/30 rounded text-2xs font-semibold">Resolve</button>` : ''}
              </td>
            </tr>
          `).join('');
        })
        .catch(err => console.error('Filter error:', err));
    });
  }
});
