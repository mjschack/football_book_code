const statusEl = document.getElementById("global-status");

function setStatus(msg, isError) {
  statusEl.textContent = msg;
  statusEl.style.color = isError ? "#d1453d" : "";
}

// Tabs
document.querySelectorAll("nav.tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav.tabs button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => (p.hidden = true));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).hidden = false;
    if (btn.dataset.tab === "model-info") loadModelInfo();
  });
});

async function postJSON(url, body) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed (${resp.status})`);
  }
  return resp.json();
}

function renderRows(container, rows) {
  container.innerHTML = "";
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    container.appendChild(row);
  });
  container.classList.add("show");
}

document.getElementById("rs-result").dataset.kind = "ryoe-simple";

document.querySelectorAll("button.run").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const resultEl = document.getElementById(btn.dataset.result);
    try {
      setStatus("Calculating...");
      let body, data;
      switch (btn.dataset.endpoint) {
        case "/api/ryoe-simple":
          body = { ydstogo: document.getElementById("rs-ydstogo").value };
          data = await postJSON(btn.dataset.endpoint, body);
          resultEl.innerHTML = `<div class="big">${data.expected_rushing_yards} yds</div>`;
          resultEl.classList.add("show");
          break;

        case "/api/ryoe-multi": {
          const actual = document.getElementById("rm-actual").value;
          body = {
            down: document.getElementById("rm-down").value,
            ydstogo: document.getElementById("rm-ydstogo").value,
            yardline_100: document.getElementById("rm-yardline100").value,
            run_location: document.getElementById("rm-location").value,
            score_differential: document.getElementById("rm-scorediff").value,
            actual_yards: actual,
          };
          data = await postJSON(btn.dataset.endpoint, body);
          resultEl.innerHTML = `<div class="big">${data.expected_rushing_yards} yds expected</div>`;
          if (data.ryoe !== undefined) {
            const rows = document.createElement("div");
            renderRows(rows, [["RYOE (actual - expected)", `${data.ryoe} yds`]]);
            resultEl.appendChild(rows);
          }
          resultEl.classList.add("show");
          break;
        }

        case "/api/completion-simple":
          body = { air_yards: document.getElementById("cs-airyards").value };
          data = await postJSON(btn.dataset.endpoint, body);
          resultEl.innerHTML = `<div class="big">${(data.completion_probability * 100).toFixed(1)}%</div>`;
          resultEl.classList.add("show");
          break;

        case "/api/completion-multi": {
          const completed = document.getElementById("cm-completed").value;
          body = {
            down: document.getElementById("cm-down").value,
            ydstogo: document.getElementById("cm-ydstogo").value,
            yardline_100: document.getElementById("cm-yardline100").value,
            air_yards: document.getElementById("cm-airyards").value,
            pass_location: document.getElementById("cm-location").value,
            qb_hit: document.getElementById("cm-qbhit").value,
            completed: completed,
          };
          data = await postJSON(btn.dataset.endpoint, body);
          resultEl.innerHTML = `<div class="big">${(data.completion_probability * 100).toFixed(1)}%</div>`;
          if (data.cpoe !== undefined) {
            const rows = document.createElement("div");
            renderRows(rows, [["CPOE (actual - expected)", `${(data.cpoe * 100).toFixed(1)} pts`]]);
            resultEl.appendChild(rows);
          }
          resultEl.classList.add("show");
          break;
        }

        case "/api/pass-td": {
          body = {
            pass_td_rate: document.getElementById("pt-rate").value,
            total_line: document.getElementById("pt-total").value,
          };
          data = await postJSON(btn.dataset.endpoint, body);
          resultEl.innerHTML = `<div class="big">${data.expected_pass_td} expected TD passes</div>`;
          const rows = document.createElement("div");
          renderRows(rows, [
            ["P(0 TD passes)", `${(data.p0 * 100).toFixed(1)}%`],
            ["P(1 TD pass)", `${(data.p1 * 100).toFixed(1)}%`],
            ["P(2 TD passes)", `${(data.p2 * 100).toFixed(1)}%`],
            ["P(3+ TD passes)", `${(data.p_ge3 * 100).toFixed(1)}%`],
          ]);
          resultEl.appendChild(rows);
          resultEl.classList.add("show");
          break;
        }
      }
      setStatus("");
    } catch (err) {
      setStatus(err.message, true);
    }
  });
});

let modelInfoLoaded = false;
async function loadModelInfo() {
  if (modelInfoLoaded) return;
  const body = document.getElementById("model-info-body");
  try {
    const resp = await fetch("/api/model-info");
    const data = await resp.json();
    body.innerHTML = "";
    Object.entries(data).forEach(([name, meta]) => {
      const section = document.createElement("div");
      section.style.marginBottom = "18px";
      const rSq = meta.r_squared !== null && meta.r_squared !== undefined ? meta.r_squared.toFixed(4) : "n/a (GLM)";
      let rowsHtml = `<tr><th>observations</th><td>${meta.n_obs}</td></tr><tr><th>R²</th><td>${rSq}</td></tr>`;
      Object.entries(meta.params).forEach(([param, val]) => {
        rowsHtml += `<tr><th>${param}</th><td>${val}</td></tr>`;
      });
      section.innerHTML = `<h3 style="font-size:0.95rem;margin-bottom:6px;">${name}</h3><table class="meta">${rowsHtml}</table>`;
      body.appendChild(section);
    });
    modelInfoLoaded = true;
  } catch (err) {
    body.textContent = "Failed to load model info: " + err.message;
  }
}
