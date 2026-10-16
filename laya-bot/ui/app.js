/**
 * app.js - Multi-Game Frontend for Laya Decision Engine Dashboard
 */

let activeGame = "tictactoe";
let gameStates = {
  tictactoe: null,
  connect4: null,
  eight_puzzle: null,
  2048: null,
};

document.addEventListener("DOMContentLoaded", () => {
  fetchGameState("tictactoe");
  loadBenchmarks();
  refreshLogs();
  setInterval(refreshLogs, 4000);
});

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function switchTab(tabId) {
  // Update tab panes
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"));
  const targetPane = document.getElementById(`pane-${tabId}`);
  if (targetPane) targetPane.classList.add("active");

  // Update tab buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"));
  const targetBtn = document.getElementById(`tab-btn-${tabId}`);
  if (targetBtn) targetBtn.classList.add("active");

  // Update rail items
  document.querySelectorAll(".rail-item").forEach((item) => item.classList.remove("active"));
  const targetRail = document.getElementById(`rail-${tabId}`);
  if (targetRail) targetRail.classList.add("active");

  if (["tictactoe", "connect4", "eight_puzzle", "2048"].includes(tabId)) {
    activeGame = tabId;
    const names = {
      tictactoe: "Tic-Tac-Toe (3x3)",
      connect4: "Connect Four (7x6)",
      eight_puzzle: "8-Puzzle (Sliding Tiles)",
      2048: "2048 (4x4 Grid)",
    };
    document.getElementById("active-game-display").innerText = names[tabId] || tabId;
    fetchGameState(tabId);
  } else if (tabId === "benchmarks") {
    loadBenchmarks();
  } else if (tabId === "logs") {
    refreshLogs();
  }
}

/* ==========================================================================
   State Fetching & Multi-Game Dispatcher
   ========================================================================== */
async function fetchGameState(gameName) {
  try {
    const res = await fetch(`/api/state?game=${gameName}`);
    const data = await res.json();
    gameStates[gameName] = data;

    updateStatusStrip(gameName, data);

    if (gameName === "tictactoe") {
      renderTicTacToe(data);
    } else if (gameName === "connect4") {
      renderConnect4(data);
    } else if (gameName === "eight_puzzle") {
      renderEightPuzzle(data);
    } else if (gameName === "2048") {
      render2048(data);
    }
  } catch (err) {
    console.error(`Failed to fetch state for ${gameName}:`, err);
  }
}

function updateStatusStrip(gameName, data) {
  const isOver = data.state.is_game_over;
  const statusEl = document.getElementById("status-display");
  const turnEl = document.getElementById("turn-display");
  const kpiEl = document.getElementById("kpi-display");

  if (isOver) {
    statusEl.innerText = `Game Over: ${String(data.state.result || "Finished").toUpperCase()}`;
  } else {
    statusEl.innerText = "Ready for Move";
  }

  if (gameName === "tictactoe" || gameName === "connect4") {
    turnEl.innerText = `Turn ${data.state.turn_number} (${data.state.current_player} Turn)`;
    kpiEl.innerText = `Legal Moves: ${data.legal_moves.length}`;
  } else if (gameName === "eight_puzzle") {
    turnEl.innerText = `Steps: ${data.state.steps_taken}`;
    kpiEl.innerText = `Manhattan Dist: ${data.manhattan} (Opt A*: ${data.optimal_steps})`;
  } else if (gameName === "2048") {
    turnEl.innerText = `Turns: ${data.state.steps_taken}`;
    kpiEl.innerText = `Score: ${data.score} · Max Tile: ${data.max_tile}`;
  }
}

/* ==========================================================================
   Game 1: Tic-Tac-Toe Renderer
   ========================================================================== */
function renderTicTacToe(data) {
  const board = data.state.board;
  const legal = data.legal_moves;
  const chosen = data.chosen_move;
  const probs = data.probabilities || {};

  const container = document.getElementById("ttt-board-grid");
  container.innerHTML = "";

  for (let i = 0; i < 9; i++) {
    const cell = document.createElement("div");
    cell.className = "board-cell";
    if (legal.includes(i)) cell.classList.add("legal");
    if (chosen === i) cell.classList.add("chosen");

    const idx = document.createElement("span");
    idx.className = "cell-index";
    idx.innerText = i;
    cell.appendChild(idx);

    const val = board[i];
    if (val && val !== " ") {
      const mark = document.createElement("div");
      mark.className = `cell-mark ${val}`;
      mark.innerText = val;
      cell.appendChild(mark);
    } else if (probs[i] !== undefined) {
      const probBadge = document.createElement("div");
      probBadge.className = "cell-prob";
      probBadge.innerText = `${(probs[i] * 100).toFixed(0)}%`;
      cell.appendChild(probBadge);
    }

    container.appendChild(cell);
  }

  renderProbabilitiesPanel("ttt-prob-bars-container", probs, chosen, "Cell");
}

/* ==========================================================================
   Game 2: Connect Four Renderer (7x6)
   ========================================================================== */
function renderConnect4(data) {
  const board = data.state.board; // 6 rows (0=bottom, 5=top), 7 cols
  const legal = data.legal_moves;
  const chosen = data.chosen_move;
  const probs = data.probabilities || {};

  // Render Column Buttons
  const btnContainer = document.getElementById("c4-col-buttons");
  btnContainer.innerHTML = "";
  for (let c = 0; c < 7; c++) {
    const btn = document.createElement("button");
    btn.className = "c4-col-btn";
    btn.innerText = `C${c}`;
    btn.disabled = !legal.includes(c) || data.state.is_game_over;
    btn.title = `Drop in column ${c}`;
    btnContainer.appendChild(btn);
  }

  // Render 6x7 Grid (displayed top to bottom: row 5 down to 0)
  const boardContainer = document.getElementById("c4-board-grid");
  boardContainer.innerHTML = "";

  for (let r = 5; r >= 0; r--) {
    for (let c = 0; c < 7; c++) {
      const slot = document.createElement("div");
      slot.className = "c4-slot";

      const val = board[r][c];
      if (val === "X" || val === "O") {
        const disc = document.createElement("div");
        disc.className = `c4-disc ${val}`;
        slot.appendChild(disc);
      }
      boardContainer.appendChild(slot);
    }
  }

  renderProbabilitiesPanel("c4-prob-bars-container", probs, chosen, "Col");
}

/* ==========================================================================
   Game 3: 8-Puzzle Renderer (3x3 Sliding)
   ========================================================================== */
function renderEightPuzzle(data) {
  const board = data.state.board; // 3x3 list of ints
  const legal = data.legal_moves;
  const chosen = data.chosen_move;
  const probs = data.probabilities || {};

  const distTag = document.getElementById("puz-distance-tag");
  if (distTag) {
    distTag.innerText = `Dist: ${data.manhattan} · Opt: ${data.optimal_steps} steps`;
  }

  const container = document.getElementById("puz-board-grid");
  container.innerHTML = "";

  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 3; c++) {
      const val = board[r][c];
      const tile = document.createElement("div");
      tile.className = "puzzle-tile";

      if (val === 0) {
        tile.classList.add("blank");
        tile.innerText = "";
      } else {
        tile.innerText = val;
        // Check if in correct goal position
        const targetR = Math.floor((val - 1) / 3);
        const targetC = (val - 1) % 3;
        if (r === targetR && c === targetC) {
          tile.classList.add("correct");
        }
      }
      container.appendChild(tile);
    }
  }

  const moveNames = { 0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT" };
  renderProbabilitiesPanel("puz-prob-bars-container", probs, chosen, "Move", moveNames);
}

/* ==========================================================================
   Game 4: 2048 Renderer (4x4 Merging Grid)
   ========================================================================== */
function render2048(data) {
  const board = data.state.board; // 4x4 list of ints
  const chosen = data.chosen_move;
  const probs = data.probabilities || {};

  const scoreTag = document.getElementById("g2048-score-tag");
  if (scoreTag) {
    scoreTag.innerText = `Score: ${data.score} · Max: ${data.max_tile}`;
  }

  const container = document.getElementById("g2048-board-grid");
  container.innerHTML = "";

  for (let r = 0; r < 4; r++) {
    for (let c = 0; c < 4; c++) {
      const val = board[r][c];
      const tile = document.createElement("div");
      tile.className = `tile-2048 val-${val}`;
      tile.innerText = val > 0 ? val : "";
      container.appendChild(tile);
    }
  }

  const moveNames = { 0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT" };
  renderProbabilitiesPanel("g2048-prob-bars-container", probs, chosen, "Slide", moveNames);
}

/* ==========================================================================
   Helper: Probabilities Visualizer Panel
   ========================================================================== */
function renderProbabilitiesPanel(containerId, probs, chosen, prefix = "Move", nameMap = null) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";

  const entries = Object.entries(probs);
  if (entries.length === 0) {
    container.innerHTML = `
      <p style="font-size: 13px; color: var(--text-muted-rose); margin-top: 10px;">
        Click "Ask Laya" to compute calibrated probabilities.
      </p>
    `;
    return;
  }

  const sorted = entries.sort((a, b) => b[1] - a[1]);

  sorted.forEach(([k, pVal]) => {
    const kNum = parseInt(k);
    const isChosen = kNum === chosen;
    const label = nameMap && nameMap[kNum] ? `${nameMap[kNum]} (${kNum})` : `${prefix} ${kNum}`;

    const item = document.createElement("div");
    item.className = "prob-item";

    const labelRow = document.createElement("div");
    labelRow.className = "prob-label-row";
    labelRow.innerHTML = `
      <span>${label} ${isChosen ? "<strong>(Selected)</strong>" : ""}</span>
      <span>${(pVal * 100).toFixed(1)}%</span>
    `;

    const track = document.createElement("div");
    track.className = "prob-bar-track";

    const fill = document.createElement("div");
    fill.className = `prob-bar-fill ${isChosen ? "highest" : ""}`;
    fill.style.width = `${Math.min(100, Math.max(0, pVal * 100))}%`;

    track.appendChild(fill);
    item.appendChild(labelRow);
    item.appendChild(track);
    container.appendChild(item);
  });
}

/* ==========================================================================
   Game Actions (Step, Auto, Reset)
   ========================================================================== */
async function stepGame(gameName) {
  const selectId = {
    tictactoe: "ttt-design-select",
    connect4: "c4-design-select",
    eight_puzzle: "puz-design-select",
    2048: "g2048-design-select",
  }[gameName];

  const design = document.getElementById(selectId)?.value || "A";
  const btn = document.querySelector(`#pane-${gameName} .btn-primary`);
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Laya Evaluating...";
  }

  try {
    const res = await fetch("/api/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game: gameName, design: design }),
    });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    gameStates[gameName] = data;
    updateStatusStrip(gameName, data);

    if (gameName === "tictactoe") renderTicTacToe(data);
    else if (gameName === "connect4") renderConnect4(data);
    else if (gameName === "eight_puzzle") renderEightPuzzle(data);
    else if (gameName === "2048") render2048(data);

    refreshLogs();
  } catch (err) {
    console.error("Step failed:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Ask Laya (1 Move)`;
    }
  }
}

async function autoPlay(gameName) {
  const selectId = {
    tictactoe: "ttt-design-select",
    connect4: "c4-design-select",
    eight_puzzle: "puz-design-select",
    2048: "g2048-design-select",
  }[gameName];

  const design = document.getElementById(selectId)?.value || "A";
  const btn = document.querySelector(`#pane-${gameName} .btn-secondary`);
  if (btn) {
    btn.disabled = true;
    btn.innerText = "Playing Automatically...";
  }

  try {
    const res = await fetch("/api/auto_game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game: gameName, design: design }),
    });
    const data = await res.json();
    gameStates[gameName] = data;
    updateStatusStrip(gameName, data);

    if (gameName === "tictactoe") renderTicTacToe(data);
    else if (gameName === "connect4") renderConnect4(data);
    else if (gameName === "eight_puzzle") renderEightPuzzle(data);
    else if (gameName === "2048") render2048(data);

    refreshLogs();
  } catch (err) {
    console.error("Auto play failed:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg> Auto-Play Game`;
    }
  }
}

async function resetGameInstance(gameName) {
  try {
    const res = await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game: gameName }),
    });
    const data = await res.json();
    gameStates[gameName] = data;
    updateStatusStrip(gameName, data);

    if (gameName === "tictactoe") renderTicTacToe(data);
    else if (gameName === "connect4") renderConnect4(data);
    else if (gameName === "eight_puzzle") renderEightPuzzle(data);
    else if (gameName === "2048") render2048(data);

    refreshLogs();
  } catch (err) {
    console.error("Reset failed:", err);
  }
}

/* ==========================================================================
   Benchmarking Tables (Table 1: Random Opponent, Table 2: Smart Random Opponent)
   ========================================================================== */
async function loadBenchmarks() {
  try {
    const res = await fetch("/api/benchmarks");
    const data = await res.json();
    renderBenchmarkTable("table-random-body", data.table_random, true);
    renderBenchmarkTable("table-smart-body", data.table_smart, false);
  } catch (err) {
    console.error("Failed to load benchmarks:", err);
  }
}

function renderBenchmarkTable(tableId, rows, isRandomTable = true) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  if (!tbody) return;
  tbody.innerHTML = "";

  const gameTagClasses = {
    "Tic-Tac-Toe": "game-tag-tictactoe",
    "Connect Four": "game-tag-connect4",
    "8-Puzzle": "game-tag-8puzzle",
    "2048": "game-tag-2048",
  };

  rows.forEach((r) => {
    const tr = document.createElement("tr");
    if (r.highlight === "gold") tr.classList.add("winner-row");

    const tagClass = gameTagClasses[r.game] || "game-tag-tictactoe";

    let marginStyle = "";
    if (r.margin.includes("+") || r.margin.includes("1.53x") || r.margin.includes("1.00x")) {
      marginStyle = "color: #4E9B68; font-weight: 700;";
    } else if (r.margin.includes("-") || r.margin.includes("Timeout")) {
      marginStyle = "color: #E53935; font-weight: 600;";
    }

    let statusBadge = "";
    if (r.status === "Winner" || r.status === "Score Winner") {
      statusBadge = `<span class="badge-winner">${r.status}</span>`;
    } else if (r.status.includes("Token")) {
      statusBadge = `<span class="badge-efficient">${r.status}</span>`;
    } else if (r.status.includes("Baseline")) {
      statusBadge = `<span class="badge-baseline">${r.status}</span>`;
    } else {
      statusBadge = `<span style="font-size: 11px; color: var(--text-muted-rose);">${r.status}</span>`;
    }

    if (isRandomTable) {
      tr.innerHTML = `
        <td><span class="game-tag ${tagClass}">${r.game}</span></td>
        <td><strong>${r.setting}</strong></td>
        <td style="font-size: 12.5px; color: var(--text-muted-rose);">${r.type}</td>
        <td>${r.wins}</td>
        <td>${r.draws}</td>
        <td>${r.losses}</td>
        <td><strong>${r.win_pct}</strong></td>
        <td style="${marginStyle}">${r.margin}</td>
        <td>${statusBadge}</td>
      `;
    } else {
      tr.innerHTML = `
        <td><span class="game-tag ${tagClass}">${r.game}</span></td>
        <td><strong>${r.setting}</strong></td>
        <td style="font-size: 12.5px; color: var(--text-muted-rose);">${r.type}</td>
        <td>${r.wins}</td>
        <td>${r.draws}</td>
        <td>${r.losses}</td>
        <td><strong>${r.win_pct}</strong></td>
        <td style="${marginStyle}">${r.margin}</td>
        <td>${statusBadge}</td>
      `;
    }

    tbody.appendChild(tr);
  });
}

/* ==========================================================================
   Logs & Audit Stream
   ========================================================================== */
async function refreshLogs() {
  try {
    const res = await fetch("/api/logs");
    const data = await res.json();
    const container = document.getElementById("logs-container");
    if (!container) return;
    container.innerHTML = "";

    data.logs.slice(-20).reverse().forEach((entry) => {
      const row = document.createElement("div");
      row.className = "log-entry";

      const timeStr = new Date(entry.timestamp * 1000).toLocaleTimeString();
      let summary = "";

      if (entry.event === "laya_call") {
        const probs = entry.data.probabilities || {};
        const pSummary = Object.entries(probs)
          .map(([k, v]) => `m${k}:${(v * 100).toFixed(0)}%`)
          .join(" ");
        summary = `Queried Laya [${pSummary}]`;
      } else if (entry.event === "decision") {
        summary = `Chosen move ${entry.data.chosen_move}`;
      } else if (entry.event === "move_sent") {
        summary = `Submitted move ${entry.data.move}`;
      } else if (entry.event === "game_start") {
        summary = `Game started (${entry.data.player || "Player"})`;
      } else if (entry.event === "game_end") {
        summary = `Game ended: ${entry.data.result}`;
      } else {
        summary = JSON.stringify(entry.data).substring(0, 80);
      }

      row.innerHTML = `
        <span class="log-ts">${timeStr}</span>
        <span class="log-tag">[${entry.event}]</span>
        <span class="log-body">${summary}</span>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    console.error("Failed to refresh logs:", err);
  }
}
