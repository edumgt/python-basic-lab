const taskSelect = document.getElementById("task-select");
const argsInput = document.getElementById("args-input");
const cwdInput = document.getElementById("cwd-input");
const stdinInput = document.getElementById("stdin-input");
const runBtn = document.getElementById("run-btn");
const refreshBtn = document.getElementById("refresh-btn");
const runStatus = document.getElementById("run-status");
const jobsEl = document.getElementById("jobs");

async function api(path, init = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `request failed: ${response.status}`);
  }
  return response.json();
}

function splitArgs(text) {
  return text
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

function formatJob(job) {
  const command = job.command.join(" ");
  const stdout = job.stdout || "";
  const stderr = job.stderr || "";
  return `
    <div class="job">
      <div><strong>${job.task_id}</strong> <span class="muted">(${job.status})</span></div>
      <div class="muted">id: ${job.id}</div>
      <div class="muted">cwd: ${job.cwd}</div>
      <div class="muted">command: ${command}</div>
      <div class="muted">return code: ${job.return_code ?? "-"}</div>
      <pre>${stdout || "[no stdout]"}</pre>
      ${stderr ? `<pre>${stderr}</pre>` : ""}
    </div>
  `;
}

async function loadTasks() {
  const tasks = await api("/api/tasks");
  taskSelect.innerHTML = "";
  for (const task of tasks) {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = `${task.id} - ${task.description}`;
    taskSelect.appendChild(option);
  }
}

async function loadJobs() {
  const jobs = await api("/api/jobs");
  jobsEl.innerHTML = jobs.length
    ? jobs.map(formatJob).join("")
    : "<p class='muted'>No jobs yet.</p>";
}

async function runTask() {
  runStatus.textContent = "Submitting...";
  const payload = {
    task_id: taskSelect.value,
    args: splitArgs(argsInput.value),
    cwd: cwdInput.value.trim() || ".",
  };
  const stdinText = stdinInput.value;
  if (stdinText.trim()) {
    payload.stdin = stdinText.endsWith("\n") ? stdinText : `${stdinText}\n`;
  }

  try {
    const job = await api("/api/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    runStatus.textContent = `Submitted job: ${job.id}`;
    await loadJobs();
  } catch (error) {
    runStatus.textContent = `Error: ${error.message}`;
  }
}

runBtn.addEventListener("click", runTask);
refreshBtn.addEventListener("click", loadJobs);

async function bootstrap() {
  try {
    await loadTasks();
    await loadJobs();
  } catch (error) {
    runStatus.textContent = `Bootstrap error: ${error.message}`;
  }
}

bootstrap();
setInterval(loadJobs, 5000);
