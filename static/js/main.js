'use strict';

const plannedList    = document.getElementById('plannedList');
const realList       = document.getElementById('realList');
const inversionPairs = document.getElementById('inversionPairs');
const busStage       = document.getElementById('busStage');
const invTrace       = document.getElementById('invTrace');
const momTrace       = document.getElementById('momTrace');

const statusCard      = document.getElementById('statusCard');
const statusIndicator = document.getElementById('statusIndicator');
const statusText      = document.getElementById('statusText');

const invCount  = document.getElementById('invCount');
const invMax    = document.getElementById('invMax');
const chaosBar  = document.getElementById('chaosBar');
const chaosPct  = document.getElementById('chaosPct');

const medianVal    = document.getElementById('medianVal');
const delayStrip   = document.getElementById('delayStrip');

const chaosSlider    = document.getElementById('chaosSlider');
const btnSimulate    = document.getElementById('btnSimulate');
const loadingOverlay = document.getElementById('loadingOverlay');

const infoFab      = document.getElementById('infoFab');
const modalOverlay = document.getElementById('modalOverlay');
const modalClose   = document.getElementById('modalClose');

let currentData = null;
const BUS_EMOJI = ['🚌','🚎','🚐','🚍','🏎','🚑','🚒','🚛'];
let emojiMap = {};

function setLoading(on) { loadingOverlay.classList.toggle('active', on); }
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

function delayColor(minutes) {
  if (minutes < 0)  return ['var(--blue)',   'delay-early'];
  if (minutes <= 5) return ['var(--green)',  'delay-ok'];
  if (minutes <= 15)return ['var(--orange)', 'delay-late'];
  return               ['var(--red)',    'delay-crisis'];
}

function delayLabel(minutes) {
  if (minutes < 0)  return `${Math.abs(minutes)}min adiantado`;
  if (minutes === 0)return 'No horário';
  return `${minutes}min de atraso`;
}

function renderOrderLists(scenario, inversionPairsArr) {
  const { planned, real, buses } = scenario;
  const invertedReal = new Set();
  inversionPairsArr.forEach(([a, b]) => { invertedReal.add(a); invertedReal.add(b); });

  plannedList.innerHTML = '';
  planned.forEach(id => {
    const bus = buses[id];
    const li  = document.createElement('li');

    li.innerHTML = `
      <span class="bus-badge" style="background:${bus.color}"></span>
      <span class="bus-num">${id}</span>
    `;
    plannedList.appendChild(li);
  });

  realList.innerHTML = '';
  real.forEach(id => {
    const bus      = buses[id];
    const inverted = invertedReal.has(id);
    const li       = document.createElement('li');
    if (inverted) li.classList.add('inverted');
    li.innerHTML = `
      <span class="bus-badge" style="background:${bus.color}"></span>
      <span class="bus-num">${id}</span>
      ${inverted ? '•' : ''}
    `;
    realList.appendChild(li);
  });

  inversionPairs.innerHTML = '';
  if (inversionPairsArr.length === 0) {
    inversionPairs.innerHTML = '<span style="font-size:0.7rem;color:var(--text-dim);">Nenhuma inversão</span>';
  } else {
    inversionPairsArr.slice(0, 10).forEach(([a, b]) => {
      const chip = document.createElement('span');
      chip.className = 'inv-pair-chip is-inverted';
      chip.textContent = `${a} / ${b}`;
      inversionPairs.appendChild(chip);
    });
  }
}

function renderBusStage(scenario, inversionPairsArr, delays) {
  const { real, buses } = scenario;
  const invertedSet = new Set();
  inversionPairsArr.forEach(([a, b]) => { invertedSet.add(a); invertedSet.add(b); });
  busStage.innerHTML = '';

  real.forEach((id, idx) => {
    const bus      = buses[id];
    const delayMin = delays[idx];
    const [dColor, dClass] = delayColor(delayMin);
    const isInverted = invertedSet.has(id);
    const emoji    = emojiMap[id] || '🚌';

    const row = document.createElement('div');
    row.className = `bus-row ${isInverted ? 'inverted-row' : 'on-time-row'}`;
    const delayStr = delayMin >= 0 ? `+${delayMin}m` : `${delayMin}m`;

    row.innerHTML = `
      <div class="bus-pos-num">${idx + 1}</div>
      <div class="bus-card">
        <div class="bus-color-block">${emoji}</div>
        <div>
          <div class="bus-line-num">${id}</div>
          <div class="bus-line-name">${bus.name.split(' - ')[1] || bus.name}</div>
        </div>
      </div>
      <div class="bus-delay-badge ${dClass}">${delayStr}</div>
      <div>
        <span class="bus-status-chip ${isInverted ? 'chip-inv' : 'chip-ok'}">
          ${isInverted ? 'INVERTIDO' : 'OK'}
        </span>
      </div>
    `;
    busStage.appendChild(row);
  });
}

function renderInversionTrace(steps) {
  invTrace.innerHTML = '';
  if (!steps || steps.length === 0) return;
  steps.forEach(step => {
    if (step.type === 'inversion') {
      const line = document.createElement('div');
      line.className = 'trace-line trace-inversion';
      line.textContent = `Inversão: pos[${step.left_val}] > pos[${step.right_val}] → +${step.count}`;
      invTrace.appendChild(line);
    }
  });
}

function renderMomTrace(steps, median) {
  momTrace.innerHTML = '';
  if (!steps || steps.length === 0) {
    momTrace.innerHTML = '<span class="trace-hint">Execute uma simulação para ver o rastreio do algoritmo...</span>';
    return;
  }

  steps.forEach(step => {
    const line = document.createElement('div');
    line.className = 'trace-line';

    if (step.type === 'split_groups') {
      line.textContent = `Dividir em grupos: ${step.groups.map(g => `[${g.join(',')}]`).join(' ')}`;
    } else if (step.type === 'group_medians') {
      line.textContent = `Medianas dos grupos: [${step.medians.join(', ')}]`;
    } else if (step.type === 'pivot_chosen') {
      line.className += ' trace-pivot';
      line.textContent = `Pivô escolhido: ${step.pivot} min`;
    } else if (step.type === 'partition') {
      line.textContent = `Partição: menores[${step.low.join(',')}] | maiores[${step.high.join(',')}]`;
    } else if (step.type === 'base_case') {
      line.textContent = `Caso base: ordenar [${step.group.join(',')}] → mediana = ${step.chosen}`;
    }

    if (line.textContent) {
      momTrace.appendChild(line);
    }
  });

  const result = document.createElement('div');
  result.className = 'trace-line trace-pivot';
  result.style.fontWeight = '600';
  result.textContent = `Mediana final calculada = ${median} minutos`;
  momTrace.appendChild(result);
}

function renderStatus(statusLevel, status) {
  statusCard.className  = `status-card ${statusLevel}`;
  statusText.textContent = status;
}

function renderInversionMetrics(data) {
  const { count, max_possible, chaos_percent } = data;
  invCount.textContent = count;
  invMax.textContent = max_possible;
  chaosBar.style.width = `${Math.min(chaos_percent, 100)}%`;
  chaosPct.textContent = `${chaos_percent}% de desorganização`;
}

function renderDelayStrip(delays, medianValue) {
  delayStrip.innerHTML = '';
  if (!delays || delays.length === 0) return;
  
  const maxAbs = Math.max(...delays.map(Math.abs), 1);
  
  delays.forEach(d => {
    const bar  = document.createElement('div');
    bar.className  = 'delay-bar';
    
    bar.dataset.tip = delayLabel(d);

    const heightPct = (Math.abs(d) / maxAbs) * 100;
    const [color]   = delayColor(d);
    
    bar.style.height     = `${Math.max(heightPct, 15)}%`;
    bar.style.background = color;
    
    if (d === medianValue) bar.classList.add('is-median');
    
    delayStrip.appendChild(bar);
  });
}

async function runSimulation() {
  const chaosLevel = chaosSlider.value / 100;
  setLoading(true);
  btnSimulate.disabled = true;

  try {
    const res  = await fetch('/api/simulate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ chaos_level: chaosLevel })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentData = data;

    const busIds = Object.keys(data.scenario.buses);
    busIds.forEach((id, i) => { emojiMap[id] = BUS_EMOJI[i % BUS_EMOJI.length]; });

    setLoading(false);
    renderStatus(data.status_level, data.status);
    renderOrderLists(data.scenario, data.inversions.pairs);
    renderBusStage(data.scenario, data.inversions.pairs, data.median.delays);
    renderInversionMetrics(data.inversions);
    renderDelayStrip(data.median.delays, data.median.value);
    medianVal.textContent = data.median.value;
    renderInversionTrace(data.inversions.steps);
    renderMomTrace(data.median.steps, data.median.value);
  } catch (err) {
    setLoading(false);
    statusText.textContent = 'ERRO';
    statusCard.className = 'status-card critical';
  } finally {
    btnSimulate.disabled = false;
  }
}

btnSimulate.addEventListener('click', runSimulation);
window.addEventListener('DOMContentLoaded', () => setTimeout(runSimulation, 200));

infoFab.addEventListener('click', () => modalOverlay.classList.add('open'));
modalClose.addEventListener('click', () => modalOverlay.classList.remove('open'));
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) modalOverlay.classList.remove('open'); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') modalOverlay.classList.remove('open'); });