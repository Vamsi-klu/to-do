class SoundEffects {
  constructor() {
    this.audioContext = null;
    this.isEnabled = true;
    this.initAudioContext();
  }

  initAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.warn('Web Audio API not supported');
      this.isEnabled = false;
    }
  }

  async resumeAudioContext() {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }
  }

  createOscillator(frequency, type = 'sine') {
    if (!this.isEnabled) return null;
    
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);
    
    oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
    oscillator.type = type;
    
    return { oscillator, gainNode };
  }

  async playCreateSound() {
    await this.resumeAudioContext();
    if (!this.isEnabled) return;

    const { oscillator, gainNode } = this.createOscillator(800, 'sine');
    if (!oscillator) return;

    const currentTime = this.audioContext.currentTime;
    
    // Volume envelope
    gainNode.gain.setValueAtTime(0, currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.01, currentTime + 0.3);
    
    // Frequency sweep
    oscillator.frequency.setValueAtTime(800, currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(1200, currentTime + 0.1);
    oscillator.frequency.exponentialRampToValueAtTime(1000, currentTime + 0.3);
    
    oscillator.start(currentTime);
    oscillator.stop(currentTime + 0.3);
  }

  async playCompleteSound() {
    await this.resumeAudioContext();
    if (!this.isEnabled) return;

    // Play a cheerful ascending arpeggio
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
    const baseTime = this.audioContext.currentTime;
    
    notes.forEach((frequency, index) => {
      const { oscillator, gainNode } = this.createOscillator(frequency, 'sine');
      if (!oscillator) return;

      const startTime = baseTime + (index * 0.1);
      const duration = 0.4;
      
      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(0.2, startTime + 0.02);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + duration);
    });
  }

  async playDeleteSound() {
    await this.resumeAudioContext();
    if (!this.isEnabled) return;

    const { oscillator, gainNode } = this.createOscillator(400, 'square');
    if (!oscillator) return;

    const currentTime = this.audioContext.currentTime;
    
    // Volume envelope
    gainNode.gain.setValueAtTime(0, currentTime);
    gainNode.gain.linearRampToValueAtTime(0.2, currentTime + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.01, currentTime + 0.4);
    
    // Descending frequency
    oscillator.frequency.setValueAtTime(400, currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(200, currentTime + 0.4);
    
    oscillator.start(currentTime);
    oscillator.stop(currentTime + 0.4);
  }

  async playCelebrationSound() {
    await this.resumeAudioContext();
    if (!this.isEnabled) return;

    // Play a triumphant fanfare
    const melodyNotes = [
      { freq: 523.25, time: 0 },    // C5
      { freq: 659.25, time: 0.15 }, // E5
      { freq: 783.99, time: 0.3 },  // G5
      { freq: 1046.5, time: 0.45 }, // C6
      { freq: 1318.5, time: 0.6 }   // E6
    ];
    
    const baseTime = this.audioContext.currentTime;
    
    melodyNotes.forEach(({ freq, time }) => {
      const { oscillator, gainNode } = this.createOscillator(freq, 'triangle');
      if (!oscillator) return;

      const startTime = baseTime + time;
      const duration = 0.3;
      
      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.05);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + duration);
    });
  }

  toggle() {
    this.isEnabled = !this.isEnabled;
    return this.isEnabled;
  }
}

// Export for use in other scripts
window.SoundEffects = SoundEffects;