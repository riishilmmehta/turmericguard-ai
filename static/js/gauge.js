/**
 * TurmericGuard AI — Radial Purity Spring Gauge (Section 8.2)
 * High-performance HTML5 Canvas gauge with spring physics easing
 * and continuous color interpolation (Red -> Amber -> Green).
 */

class PurityRadialGauge {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');

    this.options = Object.assign({
      radius: 75,
      lineWidth: 12,
      startAngle: 0.75 * Math.PI,
      endAngle: 2.25 * Math.PI,
      animationDuration: 1400,
      onUpdate: null
    }, options);

    this.currentValue = 0;
    this.targetValue = 0;
    this.animationId = null;
    this.setupCanvas();
  }

  setupCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const size = rect.width || 190;
    this.canvas.width = size * dpr;
    this.canvas.height = size * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = size;
    this.height = size;
    this.centerX = size / 2;
    this.centerY = size / 2;
  }

  interpolateColor(val) {
    // 0 -> Red, 65 -> Amber, 90+ -> Green
    let r, g, b;
    if (val < 60) {
      // Red (#ef4444: 239, 68, 68) to Amber (#f59e0b: 245, 158, 11)
      const t = Math.max(0, val / 60);
      r = Math.round(239 + (245 - 239) * t);
      g = Math.round(68 + (158 - 68) * t);
      b = Math.round(68 + (11 - 68) * t);
    } else {
      // Amber (#f59e0b) to Green (#10b981: 16, 185, 129)
      const t = Math.min(1, Math.max(0, (val - 60) / 35));
      r = Math.round(245 + (16 - 245) * t);
      g = Math.round(158 + (185 - 158) * t);
      b = Math.round(11 + (129 - 11) * t);
    }
    return `rgb(${r}, ${g}, ${b})`;
  }

  animateTo(targetVal) {
    if (!this.canvas || !this.ctx) return;
    this.targetValue = Math.max(0, Math.min(100, targetVal));
    const startVal = this.currentValue;
    const startTime = performance.now();
    const duration = this.options.animationDuration;

    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    const easeOutElastic = (t) => {
      // Smooth damped spring curve
      const p = 0.3;
      return Math.pow(2, -10 * t) * Math.sin((t - p / 4) * (2 * Math.PI) / p) + 1;
    };

    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);

      // Interpolate with eased motion
      const easedProgress = progress >= 1 ? 1 : (1 - Math.pow(1 - progress, 3));
      this.currentValue = startVal + (this.targetValue - startVal) * easedProgress;

      this.draw();

      if (this.options.onUpdate) {
        this.options.onUpdate(this.currentValue);
      }

      if (progress < 1) {
        this.animationId = requestAnimationFrame(step);
      } else {
        this.currentValue = this.targetValue;
        this.draw();
        if (this.options.onUpdate) {
          this.options.onUpdate(this.currentValue);
        }
      }
    };

    this.animationId = requestAnimationFrame(step);
  }

  draw() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    const radius = this.options.radius;
    const startA = this.options.startAngle;
    const totalAngle = this.options.endAngle - this.options.startAngle;
    const currentA = startA + (this.currentValue / 100) * totalAngle;

    // 1. Background Track Arc
    ctx.beginPath();
    ctx.arc(this.centerX, this.centerY, radius, startA, this.options.endAngle);
    ctx.lineWidth = this.options.lineWidth;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
    ctx.lineCap = 'round';
    ctx.stroke();

    // 2. Filled Value Arc with Dynamic Color
    if (this.currentValue > 0.5) {
      const activeColor = this.interpolateColor(this.currentValue);

      ctx.beginPath();
      ctx.arc(this.centerX, this.centerY, radius, startA, currentA);
      ctx.lineWidth = this.options.lineWidth;
      ctx.strokeStyle = activeColor;
      ctx.lineCap = 'round';
      ctx.shadowColor = activeColor;
      ctx.shadowBlur = 14;
      ctx.stroke();

      // Reset shadow for subsequent draws
      ctx.shadowBlur = 0;
    }

    // 3. Subtle Calibrated Radial Ticks
    const numTicks = 20;
    for (let i = 0; i <= numTicks; i++) {
      const angle = startA + (i / numTicks) * totalAngle;
      const isMajor = i % 5 === 0;
      const rInner = radius - (isMajor ? 14 : 10);
      const rOuter = radius - 6;

      const x1 = this.centerX + Math.cos(angle) * rInner;
      const y1 = this.centerY + Math.sin(angle) * rInner;
      const x2 = this.centerX + Math.cos(angle) * rOuter;
      const y2 = this.centerY + Math.sin(angle) * rOuter;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.lineWidth = isMajor ? 1.5 : 1;
      ctx.strokeStyle = isMajor ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.08)';
      ctx.stroke();
    }
  }
}
