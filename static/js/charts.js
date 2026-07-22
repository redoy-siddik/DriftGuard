// DriftGuard Chart.js Rendering Engine

document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.CHART_DATA_RAW !== 'undefined' && window.NODE_ID) {
    renderNodeDetailCharts(window.NODE_ID, window.CHART_DATA_RAW);
  }
});

function renderNodeDetailCharts(nodeId, data) {
  // Render Drift Timeline Chart
  const driftCtx = document.getElementById('nodeDriftChart');
  if (driftCtx) {
    const labels = data.labels || [];
    const compositeScores = data.composite_scores || [];

    new Chart(driftCtx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Composite Drift Score',
          data: compositeScores,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#475569',
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: '#334155', drawBorder: false },
            ticks: { color: '#94a3b8', maxTicksLimit: 12, font: { size: 10 } }
          },
          y: {
            min: 0,
            suggestedMax: 5.0,
            grid: { color: '#334155', drawBorder: false },
            ticks: { color: '#94a3b8', font: { size: 10 } }
          }
        }
      },
      plugins: [{
        id: 'referenceLines',
        beforeDraw: (chart) => {
          const { ctx, chartArea: { left, right }, scales: { y } } = chart;

          // Draw Warning line y=2.0
          const yWarn = y.getPixelForValue(2.0);
          ctx.save();
          ctx.beginPath();
          ctx.setLineDash([4, 4]);
          ctx.moveTo(left, yWarn);
          ctx.lineTo(right, yWarn);
          ctx.strokeStyle = '#f59e0b';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          // Draw Critical line y=3.5
          const yCrit = y.getPixelForValue(3.5);
          ctx.beginPath();
          ctx.setLineDash([4, 4]);
          ctx.moveTo(left, yCrit);
          ctx.lineTo(right, yCrit);
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 1.5;
          ctx.stroke();
          ctx.restore();
        }
      }]
    });
  }

  // Fetch telemetry metric snapshots for 4 metric line charts
  fetch(`/api/v1/nodes/${nodeId}/telemetry/?hours=48&limit=288`)
    .then(res => res.json())
    .then(snapshots => {
      snapshots.reverse();
      const timeLabels = snapshots.map(s => {
        const d = new Date(s.timestamp);
        return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      });

      createSparklineChart('chart-utilization', timeLabels, snapshots.map(s => s.utilization_pct), '#3b82f6', '%');
      createSparklineChart('chart-temperature', timeLabels, snapshots.map(s => s.temperature_c), '#ef4444', '°C');
      createSparklineChart('chart-power', timeLabels, snapshots.map(s => s.power_draw_w), '#f59e0b', 'W');
      createSparklineChart('chart-memory', timeLabels, snapshots.map(s => s.memory_used_gb), '#a855f7', 'GB');
    })
    .catch(err => console.error('Failed to load telemetry charts:', err));
}

function createSparklineChart(canvasId, labels, dataPoints, colorHex, unit) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        data: dataPoints,
        borderColor: colorHex,
        borderWidth: 1.5,
        fill: false,
        tension: 0.3,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `Value: ${context.parsed.y} ${unit}`
          }
        }
      },
      scales: {
        x: { display: false },
        y: {
          grid: { color: '#334155', drawBorder: false },
          ticks: { color: '#94a3b8', font: { size: 9 }, maxTicksLimit: 4 }
        }
      }
    }
  });
}
