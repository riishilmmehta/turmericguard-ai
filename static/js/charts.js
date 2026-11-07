/**
 * TurmericGuard AI — Interactive Scientific Charts (Section 8.2)
 * Chart.js wrapper for:
 * 1. 400-1000 nm Normalized Spectral Reflectance Curve with peak/trough annotations
 * 2. SHAP Feature Attribution horizontal waterfall bars
 * 3. Multi-Model Ensemble comparative probability breakdown
 */

let spectralChartInstance = null;
let shapChartInstance = null;
let ensembleChartInstance = null;

// Baseline certified authentic reference curve (Alleppey/Lakadong standard)
const PURE_REFERENCE_SPECTRA = [
  0.18, 0.16, 0.15, 0.14, 0.15, 0.17, 0.22, 0.28, 0.36, 0.45,
  0.55, 0.64, 0.72, 0.78, 0.82, 0.85, 0.87, 0.88, 0.89, 0.90,
  0.90, 0.91, 0.91, 0.92, 0.92, 0.92, 0.93, 0.93, 0.93, 0.93,
  0.94, 0.94, 0.94, 0.94, 0.94, 0.95, 0.95, 0.95, 0.95, 0.95,
  0.95, 0.95, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96, 0.96,
  0.96, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97, 0.97
];

function initOrUpdateSpectralChart(wavelengths, sampleReflectance, status) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js is not loaded, skipping spectral chart rendering.');
    return;
  }
  const ctx = document.getElementById('spectralChartCanvas');
  if (!ctx) return;

  const sampleColor = status === 'PURE' ? '#10b981' : (status === 'ADULTERATED' ? '#ef4444' : '#f59e0b');

  const data = {
    labels: wavelengths.map(wl => `${wl}nm`),
    datasets: [
      {
        label: 'Sample Measured Reflectance',
        data: sampleReflectance,
        borderColor: sampleColor,
        backgroundColor: `${sampleColor}18`,
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointBackgroundColor: sampleColor
      },
      {
        label: 'Certified Pure Reference Baseline (Spectralon 99%)',
        data: PURE_REFERENCE_SPECTRA.slice(0, wavelengths.length),
        borderColor: 'rgba(232, 163, 61, 0.45)',
        borderWidth: 1.5,
        borderDash: [5, 5],
        fill: false,
        tension: 0.35,
        pointRadius: 0
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 1200,
      easing: 'easeOutQuart'
    },
    interaction: {
      mode: 'index',
      intersect: false
    },
    plugins: {
      legend: {
        labels: {
          color: '#94a3b8',
          font: { family: 'Inter', size: 11 }
        }
      },
      tooltip: {
        backgroundColor: '#0e131f',
        borderColor: '#232c40',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#cbd5e1',
        titleFont: { family: 'JetBrains Mono', size: 12 },
        bodyFont: { family: 'JetBrains Mono', size: 11 },
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${(ctx.parsed.y * 100).toFixed(1)}% R`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#64748b',
          font: { family: 'JetBrains Mono', size: 10 },
          maxTicksLimit: 12
        },
        title: {
          display: true,
          text: 'Wavelength (nm) — Vis to Shortwave NIR',
          color: '#64748b',
          font: { family: 'Inter', size: 11 }
        }
      },
      y: {
        min: 0,
        max: 1.05,
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#64748b',
          font: { family: 'JetBrains Mono', size: 10 },
          callback: (val) => `${Math.round(val * 100)}%`
        },
        title: {
          display: true,
          text: 'Normalized Reflectance (R)',
          color: '#64748b',
          font: { family: 'Inter', size: 11 }
        }
      }
    }
  };

  if (spectralChartInstance) {
    spectralChartInstance.destroy();
  }
  spectralChartInstance = new Chart(ctx, { type: 'line', data, options });
}

function initOrUpdateShapChart(attributions) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js is not loaded, skipping SHAP chart rendering.');
    return;
  }
  const ctx = document.getElementById('shapChartCanvas');
  if (!ctx) return;

  const topAttrs = attributions.slice(0, 6);
  const labels = topAttrs.map(a => a.feature_name);
  const values = topAttrs.map(a => a.shap_value);
  const bgColors = values.map(v => v > 0 ? 'rgba(239, 68, 68, 0.85)' : 'rgba(16, 185, 129, 0.85)');

  const data = {
    labels: labels,
    datasets: [{
      label: 'SHAP Marginal Contribution (Impact on Adulteration Score)',
      data: values,
      backgroundColor: bgColors,
      borderRadius: 4,
      borderSkipped: false
    }]
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 900, easing: 'easeOutQuart' },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0e131f',
        borderColor: '#232c40',
        borderWidth: 1,
        titleColor: '#fff',
        callbacks: {
          label: (ctx) => ` Contribution: ${ctx.parsed.x > 0 ? '+' : ''}${ctx.parsed.x.toFixed(3)} (${ctx.parsed.x > 0 ? 'Adulteration Risk' : 'Purity Marker'})`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#64748b',
          font: { family: 'JetBrains Mono', size: 10 }
        },
        title: {
          display: true,
          text: '← Favors Pure Turmeric | Favors Adulterated Detection →',
          color: '#94a3b8',
          font: { family: 'Inter', size: 10 }
        }
      },
      y: {
        grid: { display: false },
        ticks: {
          color: '#f1f5f9',
          font: { family: 'Inter', size: 11 }
        }
      }
    }
  };

  if (shapChartInstance) {
    shapChartInstance.destroy();
  }
  shapChartInstance = new Chart(ctx, { type: 'bar', data, options });
}

function initOrUpdateEnsembleChart(modelBreakdowns, classes) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js is not loaded, skipping ensemble chart rendering.');
    return;
  }
  const ctx = document.getElementById('ensembleChartCanvas');
  if (!ctx) return;

  const models = Object.keys(modelBreakdowns);
  const datasets = [
    {
      label: 'Pure Turmeric',
      data: models.map(m => (modelBreakdowns[m]['pure'] * 100).toFixed(1)),
      backgroundColor: 'rgba(16, 185, 129, 0.8)'
    },
    {
      label: 'Lead Chromate (PbCrO₄)',
      data: models.map(m => (modelBreakdowns[m]['lead_chromate'] * 100).toFixed(1)),
      backgroundColor: 'rgba(239, 68, 68, 0.8)'
    },
    {
      label: 'Metanil Yellow',
      data: models.map(m => (modelBreakdowns[m]['metanil_yellow'] * 100).toFixed(1)),
      backgroundColor: 'rgba(245, 158, 11, 0.8)'
    },
    {
      label: 'Acid Orange 7',
      data: models.map(m => (modelBreakdowns[m]['acid_orange_7'] * 100).toFixed(1)),
      backgroundColor: 'rgba(217, 119, 6, 0.8)'
    },
    {
      label: 'Inert Filler',
      data: models.map(m => (modelBreakdowns[m]['starch_chalk_filler'] * 100).toFixed(1)),
      backgroundColor: 'rgba(148, 163, 184, 0.8)'
    }
  ];

  const modelLabels = {
    'xgboost_gb': 'XGBoost / GB (Primary 40%)',
    'random_forest': 'Random Forest (20%)',
    'support_vector_machine': 'SVM RBF (20%)',
    'neural_network_mlp': 'Neural Network MLP (20%)'
  };

  const data = {
    labels: models.map(m => modelLabels[m] || m),
    datasets: datasets
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        stacked: true,
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
      },
      y: {
        stacked: true,
        max: 100,
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 }, callback: v => `${v}%` }
      }
    },
    plugins: {
      legend: {
        labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
      }
    }
  };

  if (ensembleChartInstance) {
    ensembleChartInstance.destroy();
  }
  ensembleChartInstance = new Chart(ctx, { type: 'bar', data, options });
}
