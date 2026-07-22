// DriftGuard Real-time Polling & System Actions JS

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

document.addEventListener('DOMContentLoaded', () => {
  // Polling summary stats every 30 seconds
  setInterval(refreshDashboardSummary, 30000);

  // Trigger Detection Engine button handler
  const btnDetection = document.getElementById('btn-trigger-detection');
  if (btnDetection) {
    btnDetection.addEventListener('click', () => {
      btnDetection.disabled = true;
      btnDetection.classList.add('opacity-50');
      fetch('/api/v1/detection/run/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      .then(res => res.json())
      .then(data => {
        alert(`Detection pipeline executed! Processed ${data.processed} GPU nodes.`);
        location.reload();
      })
      .catch(err => alert('Detection execution failed: ' + err))
      .finally(() => {
        btnDetection.disabled = false;
        btnDetection.classList.remove('opacity-50');
      });
    });
  }

  // Trigger Training button handler
  const btnTrain = document.getElementById('btn-trigger-train');
  if (btnTrain) {
    btnTrain.addEventListener('click', () => {
      btnTrain.disabled = true;
      btnTrain.classList.add('opacity-50');
      fetch('/api/v1/detection/train/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
      })
      .then(res => res.json())
      .then(data => {
        alert(`Isolation Forest training completed! Trained: ${data.trained_nodes.length}, Skipped: ${data.skipped_nodes.length}`);
        location.reload();
      })
      .catch(err => alert('Training failed: ' + err))
      .finally(() => {
        btnTrain.disabled = false;
        btnTrain.classList.remove('opacity-50');
      });
    });
  }

  // Trigger Telemetry Generation button handler
  const btnGen = document.getElementById('btn-generate-telemetry');
  if (btnGen) {
    btnGen.addEventListener('click', () => {
      btnGen.disabled = true;
      btnGen.classList.add('opacity-50');
      fetch('/api/v1/telemetry/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ days: 7, nodes: 10, drift_pct: 0.2, clear: false })
      })
      .then(res => res.json())
      .then(data => {
        alert(`Generated ${data.created_snapshots} snapshots across ${data.node_count} nodes.`);
        location.reload();
      })
      .catch(err => alert('Telemetry generation failed: ' + err))
      .finally(() => {
        btnGen.disabled = false;
        btnGen.classList.remove('opacity-50');
      });
    });
  }

  // Single Node Train Button
  const btnTrainNode = document.getElementById('btn-train-node');
  if (btnTrainNode) {
    btnTrainNode.addEventListener('click', () => {
      const nodeId = btnTrainNode.getAttribute('data-node-id');
      fetch('/api/v1/detection/train/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ node_id: nodeId })
      })
      .then(res => res.json())
      .then(data => {
        alert(data.message);
        location.reload();
      })
      .catch(err => alert('Node training failed: ' + err));
    });
  }
});

function refreshDashboardSummary() {
  fetch('/api/v1/dashboard/summary/')
    .then(res => res.json())
    .then(data => {
      updateElemText('stat-total-nodes', data.total_nodes);
      updateElemText('stat-normal-nodes', data.nodes_normal);
      updateElemText('stat-warning-nodes', data.nodes_warning);
      updateElemText('stat-critical-nodes', data.nodes_critical);
      updateElemText('stat-open-alerts', data.open_alerts);

      const alertBadge = document.getElementById('sidebar-alert-badge');
      if (alertBadge) alertBadge.innerText = data.open_alerts;

      const lastRun = document.getElementById('nav-last-run');
      if (lastRun && data.last_detection_run) {
        lastRun.innerText = new Date(data.last_detection_run).toLocaleString();
      }
    })
    .catch(err => console.warn('Background summary poll failed:', err));
}

function updateElemText(id, val) {
  const el = document.getElementById(id);
  if (el) el.innerText = val;
}
