let activities = [];

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const data = await res.json();

    if (data.git) {
      const repoTitle = document.getElementById('activeRepoTitle');
      if (repoTitle) repoTitle.innerText = data.git.repo_name;

      // Working branch & commit status
      const branchEl = document.getElementById('repoWorkingBranch');
      if (branchEl) {
        branchEl.innerHTML = `${data.git.branch} &bull; <span class="text-zinc-500 font-normal">${data.git.tracking}</span>`;
      }

      // Latest commit / PR title
      const commitEl = document.getElementById('repoLatestCommit');
      if (commitEl) {
        commitEl.innerText = data.git.latest_commit;
      }

      // Chroma index status
      const indexStateEl = document.getElementById('repoIndexState');
      if (indexStateEl) {
        indexStateEl.innerText = data.git.index_state;
      }
      const chromaStatusEl = document.getElementById('repoChromaStatus');
      if (chromaStatusEl) {
        chromaStatusEl.innerText = data.git.chroma_status;
      }

      // Real Sandbox root directory
      const sandboxEl = document.getElementById('repoSandboxRoot');
      if (sandboxEl) {
        sandboxEl.innerText = data.git.sandbox_path;
        sandboxEl.title = data.git.sandbox_path; 
      }
    }

    activities = data.activities || [];
    renderActivities();
  } catch (err) {
    console.warn("Could not load repo status:", err);
  }
}

function renderActivities() {
  const container = document.getElementById('activityFeed');
  if (!container) return;

  if (activities.length === 0) {
    container.innerHTML = `
      <li class="text-zinc-400 text-xs py-3 text-center">No agent tasks run yet. Submit a task above.</li>
    `;
    return;
  }

  container.innerHTML = activities.map(item => `
    <li class="flex items-center justify-between pb-2.5 border-b border-zinc-100 last:border-0 last:pb-0">
      <div class="flex items-center gap-2 overflow-hidden">
        <span class="w-1.5 h-1.5 rounded-full bg-${item.color}-500 shrink-0"></span>
        <span class="font-semibold text-zinc-800 shrink-0">${item.agent}</span>
        <span class="text-zinc-600 truncate">${item.text}</span>
      </div>
      <span class="text-[11px] text-zinc-400 shrink-0 ml-2">${item.time}</span>
    </li>
  `).join('');
}

function fillSuggestion(text) {
  const input = document.getElementById('taskPrompt');
  if (input) {
    input.value = text;
    input.focus();
  }
}

document.getElementById('orchestratorForm').addEventListener('submit', async function (e) {
  e.preventDefault();
  const input = document.getElementById('taskPrompt');
  const query = input.value.trim();
  if (!query) return;

  const consoleBox = document.getElementById('executionConsole');
  const logs = document.getElementById('consoleLogs');
  const timer = document.getElementById('execTimer');
  const routeBtn = document.getElementById('routeBtn');

  consoleBox.classList.remove('hidden');
  logs.innerHTML = '';
  routeBtn.disabled = true;
  routeBtn.classList.add('opacity-50', 'cursor-not-allowed');

  const logLine = (msg, color = 'text-zinc-300') => {
    const div = document.createElement('div');
    div.className = color;
    div.innerText = msg;
    logs.appendChild(div);
    consoleBox.scrollTop = consoleBox.scrollHeight;
  };

  logLine(`[ROUTER] Evaluating request: "${query}"...`);
  logLine(`>>> Dispatching to LangGraph workflow...`, 'text-emerald-400');

  let seconds = 0;
  const timerInterval = setInterval(() => {
    seconds += 0.2;
    timer.innerText = `${seconds.toFixed(1)}s`;
  }, 200);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    clearInterval(timerInterval);

    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Agent execution failed');
    }

    const data = await res.json();

    logLine(`[NODE: ${data.agent.toUpperCase()}] Execution complete!`, 'text-emerald-300 font-bold');
    
    const finalResponse = typeof data.response === 'string' 
      ? data.response 
      : JSON.stringify(data.response, null, 2);

    logLine(`\n${finalResponse}`, 'text-zinc-100 whitespace-pre-wrap mt-2');

    if (data.activity) {
      activities.unshift(data.activity);
      renderActivities();
    }

    input.value = '';
  } catch (err) {
    clearInterval(timerInterval);
    logLine(`[ERROR]: ${err.message}`, 'text-red-400 font-bold');
  } finally {
    clearInterval(timerInterval);
    routeBtn.disabled = false;
    routeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    input.focus();
  }
});