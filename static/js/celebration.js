class CelebrationEffects {
  constructor() {
    this.isAnimating = false;
  }

  createConfetti() {
    const colors = ['#22d3ee', '#fbbf24', '#f87171', '#a78bfa', '#34d399', '#fb7185'];
    const celebration = document.createElement('div');
    celebration.className = 'celebration';
    
    // Create multiple confetti pieces
    for (let i = 0; i < 50; i++) {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = `${Math.random() * 100}vw`;
      confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDelay = `${Math.random() * 0.5}s`;
      confetti.style.animationDuration = `${2 + Math.random()}s`;
      
      // Random shapes
      if (Math.random() > 0.5) {
        confetti.style.borderRadius = '50%';
      }
      
      celebration.appendChild(confetti);
    }
    
    document.body.appendChild(celebration);
    
    // Remove after animation
    setTimeout(() => {
      if (celebration.parentNode) {
        celebration.parentNode.removeChild(celebration);
      }
    }, 3000);
  }

  showTaskCompleteText() {
    const messages = [
      '🎉 Great job!',
      '✨ Task completed!',
      '🌟 Well done!',
      '🎊 Awesome!',
      '💫 Nice work!',
      '🚀 Keep it up!'
    ];
    
    const message = messages[Math.floor(Math.random() * messages.length)];
    const textElement = document.createElement('div');
    textElement.style.cssText = `
      position: fixed;
      top: 30%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 2rem;
      font-weight: bold;
      color: var(--brand-400);
      z-index: 1001;
      pointer-events: none;
      text-shadow: 0 0 20px rgba(34, 211, 238, 0.5);
      animation: celebrationText 2s ease-out forwards;
    `;
    textElement.textContent = message;
    
    // Add keyframe animation
    if (!document.getElementById('celebration-text-style')) {
      const style = document.createElement('style');
      style.id = 'celebration-text-style';
      style.textContent = `
        @keyframes celebrationText {
          0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.5);
          }
          20% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1.2);
          }
          80% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.8);
          }
        }
      `;
      document.head.appendChild(style);
    }
    
    document.body.appendChild(textElement);
    
    setTimeout(() => {
      if (textElement.parentNode) {
        textElement.parentNode.removeChild(textElement);
      }
    }, 2000);
  }

  triggerFullCelebration() {
    if (this.isAnimating) return;
    
    this.isAnimating = true;
    
    // Show confetti
    this.createConfetti();
    
    // Show celebration text
    this.showTaskCompleteText();
    
    // Reset animation flag
    setTimeout(() => {
      this.isAnimating = false;
    }, 2000);
  }

  createFireworks() {
    const firework = document.createElement('div');
    firework.style.cssText = `
      position: fixed;
      width: 4px;
      height: 4px;
      background: var(--brand-400);
      border-radius: 50%;
      z-index: 1000;
      pointer-events: none;
    `;
    
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight * 0.5 + window.innerHeight * 0.2;
    
    firework.style.left = `${x}px`;
    firework.style.top = `${y}px`;
    
    document.body.appendChild(firework);
    
    // Animate explosion
    setTimeout(() => {
      const particles = [];
      for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
          position: fixed;
          width: 3px;
          height: 3px;
          background: ${['#22d3ee', '#fbbf24', '#f87171', '#a78bfa'][Math.floor(Math.random() * 4)]};
          border-radius: 50%;
          z-index: 1000;
          pointer-events: none;
        `;
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        
        const angle = (i / 12) * 2 * Math.PI;
        const distance = 50 + Math.random() * 50;
        const targetX = x + Math.cos(angle) * distance;
        const targetY = y + Math.sin(angle) * distance;
        
        particle.style.transition = 'all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        document.body.appendChild(particle);
        
        requestAnimationFrame(() => {
          particle.style.transform = `translate(${targetX - x}px, ${targetY - y}px)`;
          particle.style.opacity = '0';
        });
        
        particles.push(particle);
      }
      
      // Cleanup
      setTimeout(() => {
        particles.forEach(p => {
          if (p.parentNode) p.parentNode.removeChild(p);
        });
        if (firework.parentNode) firework.parentNode.removeChild(firework);
      }, 1000);
    }, 100);
  }

  triggerMultipleFireworks() {
    for (let i = 0; i < 3; i++) {
      setTimeout(() => this.createFireworks(), i * 300);
    }
  }
}

// Export for use in other scripts
window.CelebrationEffects = CelebrationEffects;