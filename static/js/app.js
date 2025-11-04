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

  function formatTimestamp(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
  }

  function render() {
    const filtered = todos.filter(t => filter === 'all' ? true : filter === 'active' ? !t.completed : t.completed);
    listEl.innerHTML = '';
    for (const t of filtered) {
      const li = document.createElement('li');
      li.className = 'task-item group py-3';
      li.dataset.taskId = t.id;

      // Main row with checkbox, text, progress
      const mainRow = document.createElement('div');
      mainRow.className = 'flex items-center gap-3';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = t.completed;
      checkbox.className = 'h-5 w-5 rounded border-slate-600 text-brand-500 bg-slate-900 flex-shrink-0';
      checkbox.addEventListener('change', async () => {
        const wasCompleted = !checkbox.checked;
        const isNowCompleted = checkbox.checked;

        if (isNowCompleted) {
          li.classList.add('task-completing');
          await soundEffects.playCompleteSound();

          setTimeout(() => {
            celebrationEffects.triggerFullCelebration();
          }, 400);
        }

        const updated = await apiPatch(t.id, { completed: checkbox.checked });
        updateTodo(updated);
        updateCounts();

        setTimeout(() => {
          li.classList.remove('task-completing');
          render();
        }, 800);
      });

      // Content wrapper
      const contentWrapper = document.createElement('div');
      contentWrapper.className = 'flex-1 min-w-0';

      // Task text
      const textWrapper = document.createElement('div');
      textWrapper.className = 'flex items-center gap-2';

      const text = document.createElement('input');
      text.value = t.text;
      text.className = 'flex-1 bg-transparent outline-none px-2 py-1 rounded focus:ring-1 focus:ring-brand-400/50 font-medium ' + (t.completed ? 'line-through text-slate-400' : '');
      text.addEventListener('change', async () => {
        const val = text.value.trim();
        if (!val) {
          text.value = t.text;
          return;
        }
        const updated = await apiPatch(t.id, { text: val });
        updateTodo(updated);
        render();
      });

      // Progress badge
      if (t.progress > 0 && !t.completed) {
        const progressBadge = document.createElement('span');
        progressBadge.className = 'text-xs px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 font-medium';
        progressBadge.textContent = `${t.progress}%`;
        textWrapper.appendChild(text);
        textWrapper.appendChild(progressBadge);
      } else {
        textWrapper.appendChild(text);
      }

      // Progress bar
      if (!t.completed && t.progress > 0) {
        const progressBar = document.createElement('div');
        progressBar.className = 'mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden';
        const progressFill = document.createElement('div');
        progressFill.className = 'h-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all duration-500';
        progressFill.style.width = `${t.progress}%`;
        progressBar.appendChild(progressFill);
        contentWrapper.appendChild(textWrapper);
        contentWrapper.appendChild(progressBar);
      } else {
        contentWrapper.appendChild(textWrapper);
      }

      // Meta info (timestamps)
      const metaInfo = document.createElement('div');
      metaInfo.className = 'flex items-center gap-3 mt-1 text-xs text-slate-400';

      const createdSpan = document.createElement('span');
      createdSpan.innerHTML = `📅 ${formatTimestamp(t.created_at)}`;
      metaInfo.appendChild(createdSpan);

      if (t.updated_at && t.updated_at !== t.created_at) {
        const updatedSpan = document.createElement('span');
        updatedSpan.innerHTML = `🔄 ${formatTimestamp(t.updated_at)}`;
        metaInfo.appendChild(updatedSpan);
      }

      if (t.notes) {
        const notesIndicator = document.createElement('span');
        notesIndicator.innerHTML = '📝 Has notes';
        notesIndicator.className = 'text-brand-400';
        metaInfo.appendChild(notesIndicator);
      }

      contentWrapper.appendChild(metaInfo);

      // Action buttons
      const actionsWrapper = document.createElement('div');
      actionsWrapper.className = 'flex items-center gap-2';

      // View Details button
      const detailsBtn = document.createElement('button');
      detailsBtn.innerHTML = '🔍';
      detailsBtn.title = 'View Details & AI Insights';
      detailsBtn.className = 'opacity-0 group-hover:opacity-100 transition text-lg hover:scale-110';
      detailsBtn.addEventListener('click', () => openTaskModal(t));

      const del = document.createElement('button');
      del.innerText = '🗑️';
      del.title = 'Delete';
      del.className = 'opacity-0 group-hover:opacity-100 transition text-lg hover:scale-110';
      del.addEventListener('click', async () => {
        li.classList.add('task-deleting');
        await soundEffects.playDeleteSound();

        setTimeout(async () => {
          await apiDelete(t.id);
          todos = todos.filter(x => x.id !== t.id);
          updateCounts();
          render();
        }, 400);
      });

      actionsWrapper.appendChild(detailsBtn);
      actionsWrapper.appendChild(del);

      mainRow.appendChild(checkbox);
      mainRow.appendChild(contentWrapper);
      mainRow.appendChild(actionsWrapper);
      li.appendChild(mainRow);
      listEl.appendChild(li);
    }

    updateCounts();
  }

  async function openTaskModal(todo) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm';
    modal.style.animation = 'fadeIn 0.2s ease-out';

    const modalContent = document.createElement('div');
    modalContent.className = 'glass rounded-2xl shadow-2xl ring-1 ring-white/10 p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto';
    modalContent.style.animation = 'slideUp 0.3s ease-out';

    // Header
    const header = document.createElement('div');
    header.className = 'flex items-start justify-between mb-6';

    const titleSection = document.createElement('div');
    titleSection.className = 'flex-1';

    const modalTitle = document.createElement('h2');
    modalTitle.className = 'text-2xl font-semibold mb-2';
    modalTitle.textContent = todo.text;

    const statusBadge = document.createElement('span');
    statusBadge.className = `inline-block px-3 py-1 rounded-full text-sm font-medium ${
      todo.completed ? 'bg-green-500/20 text-green-300' : 'bg-blue-500/20 text-blue-300'
    }`;
    statusBadge.textContent = todo.completed ? '✅ Completed' : '🔄 In Progress';

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✕';
    closeBtn.className = 'text-2xl text-slate-400 hover:text-white transition';
    closeBtn.addEventListener('click', () => modal.remove());

    titleSection.appendChild(modalTitle);
    titleSection.appendChild(statusBadge);
    header.appendChild(titleSection);
    header.appendChild(closeBtn);

    // Progress section
    const progressSection = document.createElement('div');
    progressSection.className = 'mb-6';

    const progressLabel = document.createElement('label');
    progressLabel.className = 'block text-sm font-medium mb-2';
    progressLabel.textContent = `Progress: ${todo.progress}%`;

    const progressInput = document.createElement('input');
    progressInput.type = 'range';
    progressInput.min = '0';
    progressInput.max = '100';
    progressInput.value = todo.progress;
    progressInput.className = 'w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer';

    const progressBar = document.createElement('div');
    progressBar.className = 'mt-2 h-3 bg-slate-800 rounded-full overflow-hidden';
    const progressFill = document.createElement('div');
    progressFill.className = 'h-full bg-gradient-to-r from-brand-500 to-brand-400 transition-all duration-300';
    progressFill.style.width = `${todo.progress}%`;
    progressBar.appendChild(progressFill);

    progressInput.addEventListener('input', async (e) => {
      const value = e.target.value;
      progressLabel.textContent = `Progress: ${value}%`;
      progressFill.style.width = `${value}%`;

      const updated = await apiPatch(todo.id, { progress: parseInt(value) });
      updateTodo(updated);
      render();
    });

    progressSection.appendChild(progressLabel);
    progressSection.appendChild(progressInput);
    progressSection.appendChild(progressBar);

    // Notes section
    const notesSection = document.createElement('div');
    notesSection.className = 'mb-6';

    const notesLabel = document.createElement('label');
    notesLabel.className = 'block text-sm font-medium mb-2';
    notesLabel.textContent = '📝 Notes';

    const notesTextarea = document.createElement('textarea');
    notesTextarea.className = 'w-full rounded-xl bg-slate-900/60 ring-1 ring-white/10 focus:ring-brand-400/50 outline-none px-4 py-3 min-h-[100px]';
    notesTextarea.placeholder = 'Add detailed notes about this task...';
    notesTextarea.value = todo.notes || '';
    notesTextarea.addEventListener('change', async () => {
      const updated = await apiPatch(todo.id, { notes: notesTextarea.value });
      updateTodo(updated);
      render();
    });

    notesSection.appendChild(notesLabel);
    notesSection.appendChild(notesTextarea);

    // Timestamps section
    const timestampsSection = document.createElement('div');
    timestampsSection.className = 'mb-6 grid grid-cols-2 gap-4';

    const createdCard = document.createElement('div');
    createdCard.className = 'bg-slate-900/60 rounded-lg p-3';
    createdCard.innerHTML = `
      <div class="text-xs text-slate-400 mb-1">Created</div>
      <div class="text-sm font-medium">📅 ${formatTimestamp(todo.created_at)}</div>
      <div class="text-xs text-slate-500 mt-1">${new Date(todo.created_at).toLocaleString()}</div>
    `;

    const updatedCard = document.createElement('div');
    updatedCard.className = 'bg-slate-900/60 rounded-lg p-3';
    updatedCard.innerHTML = `
      <div class="text-xs text-slate-400 mb-1">Last Updated</div>
      <div class="text-sm font-medium">🔄 ${formatTimestamp(todo.updated_at)}</div>
      <div class="text-xs text-slate-500 mt-1">${new Date(todo.updated_at).toLocaleString()}</div>
    `;

    timestampsSection.appendChild(createdCard);
    timestampsSection.appendChild(updatedCard);

    // AI Summary section
    const aiSection = document.createElement('div');
    aiSection.className = 'mb-6';

    const aiHeader = document.createElement('div');
    aiHeader.className = 'flex items-center gap-2 mb-3';
    aiHeader.innerHTML = '<h3 class="text-lg font-semibold">🤖 AI Insights</h3>';

    const aiLoadingDiv = document.createElement('div');
    aiLoadingDiv.className = 'text-center py-8 text-slate-400';
    aiLoadingDiv.innerHTML = '<div class="animate-pulse">🧠 Generating AI insights...</div>';

    aiSection.appendChild(aiHeader);
    aiSection.appendChild(aiLoadingDiv);

    // Assemble modal
    modalContent.appendChild(header);
    modalContent.appendChild(progressSection);
    modalContent.appendChild(notesSection);
    modalContent.appendChild(timestampsSection);
    modalContent.appendChild(aiSection);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });

    // Fetch and display AI summary
    try {
      const aiData = await fetch(`/api/todos/${todo.id}/ai-summary`).then(r => r.json());

      aiLoadingDiv.remove();

      // Summary
      const summaryDiv = document.createElement('div');
      summaryDiv.className = 'bg-gradient-to-r from-brand-500/10 to-purple-500/10 rounded-lg p-4 mb-4 ring-1 ring-brand-400/30';
      summaryDiv.innerHTML = `
        <div class="font-medium text-brand-300 mb-2">📊 Summary</div>
        <div class="text-sm">${aiData.summary}</div>
      `;
      aiSection.appendChild(summaryDiv);

      // Suggestions
      if (aiData.suggestions && aiData.suggestions.length > 0) {
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'mb-4';

        const suggestionsHeader = document.createElement('div');
        suggestionsHeader.className = 'font-medium text-brand-300 mb-2';
        suggestionsHeader.textContent = '💡 Smart Suggestions';
        suggestionsDiv.appendChild(suggestionsHeader);

        const suggestionsList = document.createElement('div');
        suggestionsList.className = 'space-y-2';

        aiData.suggestions.forEach(suggestion => {
          const suggestionItem = document.createElement('div');
          suggestionItem.className = 'flex items-start gap-3 bg-slate-900/60 rounded-lg p-3';
          suggestionItem.innerHTML = `
            <span class="text-2xl">${suggestion.icon}</span>
            <div class="flex-1 text-sm">${suggestion.text}</div>
          `;
          suggestionsList.appendChild(suggestionItem);
        });

        suggestionsDiv.appendChild(suggestionsList);
        aiSection.appendChild(suggestionsDiv);
      }

      // Insights
      if (aiData.insights && aiData.insights.length > 0) {
        const insightsDiv = document.createElement('div');
        insightsDiv.className = 'bg-purple-500/10 rounded-lg p-4 ring-1 ring-purple-400/30';

        const insightsHeader = document.createElement('div');
        insightsHeader.className = 'font-medium text-purple-300 mb-2';
        insightsHeader.textContent = '🎯 Insights';
        insightsDiv.appendChild(insightsHeader);

        aiData.insights.forEach(insight => {
          const insightItem = document.createElement('div');
          insightItem.className = 'text-sm mb-1';
          insightItem.textContent = `• ${insight}`;
          insightsDiv.appendChild(insightItem);
        });

        aiSection.appendChild(insightsDiv);
      }
    } catch (error) {
      aiLoadingDiv.innerHTML = '<div class="text-red-400">Failed to load AI insights</div>';
    }
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

    if (done.length > 1) {
      await soundEffects.playCelebrationSound();
      celebrationEffects.triggerMultipleFireworks();
    } else {
      await soundEffects.playDeleteSound();
    }

    const completedElements = Array.from(listEl.querySelectorAll('.task-item')).filter(el => {
      const taskId = el.dataset.taskId;
      return done.some(task => task.id == taskId);
    });

    completedElements.forEach(el => {
      el.classList.add('task-deleting');
    });

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

  themeToggle.addEventListener('click', toggleTheme);

  // Add CSS animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes slideUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  `;
  document.head.appendChild(style);

  // initial load
  (async () => {
    initTheme();
    todos = await apiList();
    render();
  })();
})();
