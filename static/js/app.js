(() => {
  const listEl = document.getElementById('list');
  const inputEl = document.getElementById('new-todo');
  const addBtn = document.getElementById('add-btn');
  const leftCountEl = document.getElementById('left-count');
  const clearCompletedBtn = document.getElementById('clear-completed');
  const filterBtns = Array.from(document.querySelectorAll('.filter-btn'));
  const themeToggle = document.getElementById('theme-toggle');

  let todos = [];
  let filter = 'all';
  
  // Initialize sound effects and celebrations
  const soundEffects = new SoundEffects();
  const celebrationEffects = new CelebrationEffects();
  
  // Theme management
  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
  }
  
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeToggleIcon(theme);
  }
  
  function updateThemeToggleIcon(theme) {
    const sunIcon = themeToggle.querySelector('.sun-icon');
    const moonIcon = themeToggle.querySelector('.moon-icon');
    
    if (theme === 'light') {
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'block';
    } else {
      sunIcon.style.display = 'block';
      moonIcon.style.display = 'none';
    }
  }
  
  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }

  function render() {
    const filtered = todos.filter(t => filter === 'all' ? true : filter === 'active' ? !t.completed : t.completed);
    listEl.innerHTML = '';
    for (const t of filtered) {
      const li = document.createElement('li');
      li.className = 'task-item group flex items-center gap-3 py-3';
      li.dataset.taskId = t.id;

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = t.completed;
      checkbox.className = 'h-5 w-5 rounded border-slate-600 text-brand-500 bg-slate-900';
      checkbox.addEventListener('change', async () => {
        const wasCompleted = !checkbox.checked;
        const isNowCompleted = checkbox.checked;
        
        // Add animation class
        if (isNowCompleted) {
          li.classList.add('task-completing');
          await soundEffects.playCompleteSound();
          
          // Trigger celebration for completing a task
          setTimeout(() => {
            celebrationEffects.triggerFullCelebration();
          }, 400);
        }
        
        const updated = await apiPatch(t.id, { completed: checkbox.checked });
        updateTodo(updated);
        updateCounts();
        
        // Remove animation class after animation completes
        setTimeout(() => {
          li.classList.remove('task-completing');
          render();
        }, 800);
      });

      const text = document.createElement('input');
      text.value = t.text;
      text.className = 'flex-1 bg-transparent outline-none px-2 py-1 rounded focus:ring-1 focus:ring-brand-400/50 ' + (t.completed ? 'line-through text-slate-400' : '');
      text.addEventListener('change', async () => {
        const val = text.value.trim();
        if (!val) {
          text.value = t.text; // revert
          return;
        }
        const updated = await apiPatch(t.id, { text: val });
        updateTodo(updated);
        render();
      });

      const del = document.createElement('button');
      del.innerText = 'Delete';
      del.className = 'opacity-0 group-hover:opacity-100 transition text-sm text-slate-300 hover:text-red-300';
      del.addEventListener('click', async () => {
        // Add delete animation
        li.classList.add('task-deleting');
        await soundEffects.playDeleteSound();
        
        // Wait for animation to complete before removing from DOM
        setTimeout(async () => {
          await apiDelete(t.id);
          todos = todos.filter(x => x.id !== t.id);
          updateCounts();
          render();
        }, 400);
      });

      li.appendChild(checkbox);
      li.appendChild(text);
      li.appendChild(del);
      listEl.appendChild(li);
    }

    updateCounts();
  }

  function updateCounts() {
    const left = todos.filter(t => !t.completed).length;
    leftCountEl.textContent = String(left);
  }

  function updateTodo(updated) {
    const idx = todos.findIndex(x => x.id === updated.id);
    if (idx !== -1) todos[idx] = updated;
  }

  async function apiList() {
    const res = await fetch('/api/todos');
    if (!res.ok) throw new Error('Failed to list todos');
    return res.json();
  }

  async function apiCreate(text) {
    const res = await fetch('/api/todos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error('Failed to create todo');
    return res.json();
  }

  async function apiPatch(id, payload) {
    const res = await fetch(`/api/todos/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update todo');
    return res.json();
  }

  async function apiDelete(id) {
    const res = await fetch(`/api/todos/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete todo');
  }

  addBtn.addEventListener('click', async () => {
    const text = inputEl.value.trim();
    if (!text) return;
    
    await soundEffects.playCreateSound();
    const created = await apiCreate(text);
    todos.unshift(created);
    inputEl.value = '';
    updateCounts();
    render();
    
    // Add create animation to the new task
    setTimeout(() => {
      const newTaskEl = listEl.querySelector(`[data-task-id="${created.id}"]`);
      if (newTaskEl) {
        newTaskEl.classList.add('task-creating');
        setTimeout(() => {
          newTaskEl.classList.remove('task-creating');
        }, 500);
      }
    }, 50);
  });

  inputEl.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      addBtn.click();
    }
  });

  clearCompletedBtn.addEventListener('click', async () => {
    const done = todos.filter(t => t.completed);
    if (done.length === 0) return;
    
    // Play celebration sound for clearing multiple completed tasks
    if (done.length > 1) {
      await soundEffects.playCelebrationSound();
      celebrationEffects.triggerMultipleFireworks();
    } else {
      await soundEffects.playDeleteSound();
    }
    
    // Animate all completed tasks being deleted
    const completedElements = Array.from(listEl.querySelectorAll('.task-item')).filter(el => {
      const taskId = el.dataset.taskId;
      return done.some(task => task.id == taskId);
    });
    
    completedElements.forEach(el => {
      el.classList.add('task-deleting');
    });
    
    // Wait for animations to complete
    setTimeout(async () => {
      for (const t of done) await apiDelete(t.id);
      todos = todos.filter(t => !t.completed);
      render();
    }, 400);
  });

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('bg-slate-800', 'text-slate-200'));
      btn.classList.add('bg-slate-800', 'text-slate-200');
      filter = btn.dataset.filter;
      render();
    })
  });

  // Theme toggle event listener
  themeToggle.addEventListener('click', toggleTheme);

  // initial load
  (async () => {
    initTheme();
    todos = await apiList();
    render();
  })();
})();

