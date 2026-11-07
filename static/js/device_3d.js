/**
 * TurmericGuard AI — 3D Sensing Enclosure Visualizer (Section 5.1 & 8.2)
 * Renders an interactive 3D model of the TurmericGuard light-sealed optical chamber:
 * - 6000K Calibrated LED Ring with diffuse light cone
 * - Standardized glass sample petri dish with turmeric spice powder
 * - 12MP Optical Imaging Sensor & AS7265x / Vis-SWNIR Spectrometer module
 * - Reference calibration tile holder
 */

class DeviceChamber3D {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.rotation = 0.35;
    this.pitch = 0.45;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;
    this.pulsePhase = 0;

    this.setupListeners();
    this.animate();
  }

  setupListeners() {
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastMouseX;
      const dy = e.clientY - this.lastMouseY;
      this.rotation += dx * 0.01;
      this.pitch = Math.max(0.1, Math.min(1.2, this.pitch + dy * 0.01));
      this.lastMouseX = e.clientX;
      this.lastMouseY = e.clientY;
    });
  }

  animate() {
    if (!this.canvas || !this.ctx) return;
    this.pulsePhase += 0.04;
    if (!this.isDragging) {
      this.rotation += 0.005; // Gentle auto-rotation
    }
    this.draw();
    requestAnimationFrame(() => this.animate());
  }

  draw() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2 + 15;

    // 1. Base Platform / Enclosure Floor
    ctx.save();
    ctx.translate(cx, cy);

    // Iso projection helper
    const isoX = (x, y) => (x * Math.cos(this.rotation) - y * Math.sin(this.rotation));
    const isoY = (x, y, z) => (x * Math.sin(this.rotation) + y * Math.cos(this.rotation)) * Math.sin(this.pitch) - z * Math.cos(this.pitch);

    // Enclosure bottom plate (Dark charcoal aluminum)
    ctx.beginPath();
    const rBase = 110;
    for (let i = 0; i <= 360; i += 15) {
      const rad = (i * Math.PI) / 180;
      const bx = isoX(Math.cos(rad) * rBase, Math.sin(rad) * rBase);
      const by = isoY(Math.cos(rad) * rBase, Math.sin(rad) * rBase, -30);
      if (i === 0) ctx.moveTo(bx, by);
      else ctx.lineTo(bx, by);
    }
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Standardized Glass Sample Tray (Petri dish)
    ctx.beginPath();
    const rDish = 65;
    for (let i = 0; i <= 360; i += 15) {
      const rad = (i * Math.PI) / 180;
      const dx = isoX(Math.cos(rad) * rDish, Math.sin(rad) * rDish);
      const dy = isoY(Math.cos(rad) * rDish, Math.sin(rad) * rDish, -15);
      if (i === 0) ctx.moveTo(dx, dy);
      else ctx.lineTo(dx, dy);
    }
    ctx.fillStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Turmeric Spice Mound (Vivid Gold Core)
    ctx.beginPath();
    const rSpice = 50;
    for (let i = 0; i <= 360; i += 15) {
      const rad = (i * Math.PI) / 180;
      const sx = isoX(Math.cos(rad) * rSpice, Math.sin(rad) * rSpice);
      const sy = isoY(Math.cos(rad) * rSpice, Math.sin(rad) * rSpice, -10);
      if (i === 0) ctx.moveTo(sx, sy);
      else ctx.lineTo(sx, sy);
    }
    const spiceGrad = ctx.createRadialGradient(0, -10, 5, 0, -10, 50);
    spiceGrad.addColorStop(0, '#f59e0b');
    spiceGrad.addColorStop(1, '#b45309');
    ctx.fillStyle = spiceGrad;
    ctx.fill();

    // Reference Calibration Tile (White Spectralon standard on the left)
    const tx = isoX(-75, 20);
    const ty = isoY(-75, 20, -15);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(tx - 10, ty - 6, 20, 12);
    ctx.strokeStyle = '#e2e8f0';
    ctx.strokeRect(tx - 10, ty - 6, 20, 12);

    // 6000K LED Ring Light Emitter (Suspended overhead)
    const rLed = 80;
    const zLed = 70;
    ctx.beginPath();
    for (let i = 0; i <= 360; i += 15) {
      const rad = (i * Math.PI) / 180;
      const lx = isoX(Math.cos(rad) * rLed, Math.sin(rad) * rLed);
      const ly = isoY(Math.cos(rad) * rLed, Math.sin(rad) * rLed, zLed);
      if (i === 0) ctx.moveTo(lx, ly);
      else ctx.lineTo(lx, ly);
    }
    ctx.strokeStyle = '#e8a33d';
    ctx.lineWidth = 3;
    ctx.shadowColor = '#e8a33d';
    ctx.shadowBlur = 12 + Math.sin(this.pulsePhase) * 4;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Optical Sensing Head (Camera + Spectrometer Module at top)
    const zHead = 110;
    const hx = isoX(0, 0);
    const hy = isoY(0, 0, zHead);

    ctx.fillStyle = '#1e293b';
    ctx.fillRect(hx - 20, hy - 14, 40, 28);
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(hx - 20, hy - 14, 40, 28);

    // Camera Lens & Spectrometer Aperture
    ctx.fillStyle = '#0284c7';
    ctx.beginPath();
    ctx.arc(hx - 8, hy, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(hx + 8, hy, 4, 0, Math.PI * 2);
    ctx.fill();

    // Projected Optical Sensing Rays (Focal Cone from Lens to Sample)
    ctx.beginPath();
    ctx.moveTo(hx - 8, hy + 5);
    ctx.lineTo(isoX(-35, -20), isoY(-35, -20, -10));
    ctx.moveTo(hx - 8, hy + 5);
    ctx.lineTo(isoX(35, 20), isoY(35, 20, -10));
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.stroke();

    // NIR Spectrometer Sensing Ray (Green beam)
    ctx.beginPath();
    ctx.moveTo(hx + 8, hy + 5);
    ctx.lineTo(isoX(0, 0), isoY(0, 0, -10));
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([]);
    ctx.stroke();

    ctx.restore();
  }
}
