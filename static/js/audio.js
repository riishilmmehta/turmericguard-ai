/**
 * TurmericGuard AI — Laboratory Web Audio Synthesizer
 * Pure native HTML5 Web Audio API sound generator. Zero external dependencies.
 * Produces futuristic sci-fi laboratory feedback: clicks, scan sweeps, success chords, and alert alarms.
 */

class LaboratoryAudioEngine {
  constructor() {
    this.ctx = null;
    this.enabled = localStorage.getItem('tg_sound_enabled') !== 'false';
  }

  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleSound() {
    this.enabled = !this.enabled;
    localStorage.setItem('tg_sound_enabled', this.enabled ? 'true' : 'false');
    this.updateUI();
    if (this.enabled) {
      this.playClick();
    }
    return this.enabled;
  }

  updateUI() {
    const btn = document.getElementById('soundToggleBtn');
    const icon = document.getElementById('soundIcon');
    const text = document.getElementById('soundText');
    if (icon) icon.textContent = this.enabled ? '🔊' : '🔇';
    if (text) text.textContent = this.enabled ? 'Sound ON' : 'Muted';
    if (btn) btn.classList.toggle('active', this.enabled);
  }

  playClick() {
    if (!this.enabled) return;
    try {
      this.ensureContext();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(440, this.ctx.currentTime + 0.05);

      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.06);
    } catch (e) {
      // Audio permission or unsupported
    }
  }

  playScan() {
    if (!this.enabled) return;
    try {
      this.ensureContext();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(320, this.ctx.currentTime);
      osc.frequency.linearRampToValueAtTime(740, this.ctx.currentTime + 0.35);

      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.35);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.36);
    } catch (e) {}
  }

  playSuccessChord() {
    if (!this.enabled) return;
    try {
      this.ensureContext();
      if (!this.ctx) return;
      // C5 (523.25), E5 (659.25), G5 (783.99), C6 (1046.50) arpeggiated major chord
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime + i * 0.08);

        gain.gain.setValueAtTime(0.07, this.ctx.currentTime + i * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + i * 0.08 + 0.45);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(this.ctx.currentTime + i * 0.08);
        osc.stop(this.ctx.currentTime + i * 0.08 + 0.46);
      });
    } catch (e) {}
  }

  playAlertBuzzer() {
    if (!this.enabled) return;
    try {
      this.ensureContext();
      if (!this.ctx) return;
      // Strobe warning dual-tone
      const times = [0, 0.14];
      times.forEach((t) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(260, this.ctx.currentTime + t);

        gain.gain.setValueAtTime(0.08, this.ctx.currentTime + t);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + t + 0.11);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(this.ctx.currentTime + t);
        osc.stop(this.ctx.currentTime + t + 0.12);
      });
    } catch (e) {}
  }
}

const laboratoryAudio = new LaboratoryAudioEngine();

function toggleAudio() {
  laboratoryAudio.toggleSound();
}

// Window namespace exports
window.laboratoryAudio = laboratoryAudio;
window.toggleAudio = toggleAudio;

function bootAudio() {
  laboratoryAudio.updateUI();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootAudio);
} else {
  bootAudio();
}
