'use strict';

(function () {
  const explorer = document.querySelector('[data-contribution-city]');
  if (!explorer) return;

  const ns = 'http://www.w3.org/2000/svg';
  const grid = explorer.querySelector('[data-city-grid]');
  const buildingsLayer = explorer.querySelector('[data-city-buildings]');
  const range = explorer.querySelector('[data-city-range]');
  const dateOutput = explorer.querySelector('[data-city-date]');
  const startLabel = explorer.querySelector('[data-city-start]');
  const endLabel = explorer.querySelector('[data-city-end]');
  const status = explorer.querySelector('[data-city-status]');
  const totalMetric = explorer.querySelector('[data-city-total]');
  const activeMetric = explorer.querySelector('[data-city-active]');
  const currentStreakMetric = explorer.querySelector('[data-city-current-streak]');
  const longestStreakMetric = explorer.querySelector('[data-city-longest-streak]');
  const selectionText = explorer.querySelector('[data-city-selection]');
  const playButton = explorer.querySelector('[data-city-play]');
  const pauseButton = explorer.querySelector('[data-city-pause]');
  const restartButton = explorer.querySelector('[data-city-restart]');
  const expandButton = explorer.querySelector('[data-city-expand]');
  const closeButton = explorer.querySelector('[data-city-close]');
  const fallback = explorer.querySelector('[data-city-fallback]');
  const scene = explorer.querySelector('[data-city-scene]');

  let days = [];
  let buildings = [];
  let buildingByIndex = new Map();
  let prefixes = [];
  let currentIndex = -1;
  let selectedIndex = -1;
  let playTimer = null;
  let fallbackExpanded = false;

  const number = new Intl.NumberFormat();

  function parseDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split('-').map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day, 12));
    if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) return null;
    return parsed;
  }

  function dateLabel(value, weekday = false) {
    const parsed = parseDate(value);
    if (!parsed) return value;
    return new Intl.DateTimeFormat(undefined, {
      timeZone: 'UTC',
      ...(weekday ? { weekday: 'short' } : {}),
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(parsed);
  }

  function daysBetween(first, second) {
    return (parseDate(second) - parseDate(first)) / 86400000;
  }

  function validatePayload(payload) {
    if (!payload || payload.schema_version !== 1 || payload.username !== 'tanishqnarula12' || !Array.isArray(payload.days)) {
      throw new Error('The contribution calendar format is not supported.');
    }
    if (payload.days.length < 300) throw new Error('The contribution calendar is incomplete.');
    let previous = '';
    return payload.days.map((item) => {
      if (!item || !parseDate(item.date) || item.date <= previous ||
          !Number.isInteger(item.count) || item.count < 0 ||
          !Number.isInteger(item.level) || item.level < 0 || item.level > 4) {
        throw new Error('The contribution calendar contains invalid daily data.');
      }
      previous = item.date;
      return { date: item.date, count: item.count, level: item.level };
    });
  }

  function svgElement(name, attrs) {
    const element = document.createElementNS(ns, name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }

  function polygon(points, className, attrs = {}) {
    const element = svgElement('polygon', {
      points: points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '),
      class: className,
      ...attrs
    });
    return element;
  }

  function cellPoints(x, y) {
    return [
      [x, y], [x + 17.5, y + 6], [x + 35, y - 4], [x + 17.5, y - 10]
    ];
  }

  function buildStats() {
    let total = 0;
    let active = 0;
    let currentStreak = 0;
    let longestStreak = 0;
    let previousDate = '';

    prefixes = days.map((day) => {
      total += day.count;
      active += day.count > 0 ? 1 : 0;
      if (day.count > 0) {
        currentStreak = previousDate && daysBetween(previousDate, day.date) === 1 ? currentStreak + 1 : 1;
        longestStreak = Math.max(longestStreak, currentStreak);
      } else {
        currentStreak = 0;
      }
      previousDate = day.date;
      return { total, active, currentStreak, longestStreak };
    });
  }

  function buildCity() {
    const startDate = parseDate(days[0].date);
    const startWeekday = startDate.getUTCDay();
    const colors = ['#10271D', '#168447', '#25B65D', '#45DB78', '#9AF2A8'];
    const maxCount = Math.max(1, ...days.map((day) => day.count));

    days.forEach((day, index) => {
      const parsedDate = parseDate(day.date);
      const weekday = parsedDate.getUTCDay();
      const week = Math.floor((index + startWeekday) / 7);
      const x = 43 + week * 17.5 + weekday * 17.5;
      const y = 240 + week * 6 - weekday * 10;
      const [a, b, c, d] = cellPoints(x, y);

      grid.appendChild(polygon([a, b, c, d], 'city-grid-cell'));
      if (day.count === 0) return;

      const height = Math.min(108, 14 + 94 * Math.pow(day.count / maxCount, 0.55));
      const top = [a, b, c, d].map(([px, py]) => [px, py - height]);
      const [at, bt, ct, dt] = top;
      const color = colors[Math.min(day.level, 4)];
      const group = svgElement('g', {
        class: 'city-building is-future',
        'data-city-building': '',
        'data-index': index,
        role: 'button',
        tabindex: '-1',
        'aria-label': `${dateLabel(day.date, true)}: ${number.format(day.count)} ${day.count === 1 ? 'contribution' : 'contributions'}`
      });

      group.appendChild(svgElement('ellipse', {
        cx: x + 14,
        cy: (y - height / 2).toFixed(1),
        rx: 14,
        ry: (height / 1.5).toFixed(1),
        fill: color,
        opacity: '.18',
        filter: 'url(#city-glow)'
      }));
      group.appendChild(polygon([a, b, bt, at], 'city-side-face', { fill: '#126539', stroke: color, 'stroke-width': '.8' }));
      group.appendChild(polygon([b, c, ct, bt], 'city-side-face', { fill: '#0A4B2A', stroke: color, 'stroke-width': '.8' }));
      group.appendChild(polygon([at, bt, ct, dt], 'city-top-face', { fill: color, stroke: '#B8FFC4', 'stroke-width': '.8' }));
      if (day.count >= Math.max(8, maxCount * .55)) {
        group.appendChild(svgElement('path', {
          d: `M${(x + 10).toFixed(1)} ${(y - height + 3).toFixed(1)}h9`,
          stroke: '#D9FFE0',
          'stroke-width': '1.5',
          opacity: '.9'
        }));
      }
      buildings.push(group);
      buildingByIndex.set(index, group);
      buildingsLayer.appendChild(group);
    });

    if (buildings.length) buildings[0].setAttribute('tabindex', '0');
  }

  function updateSelection(index) {
    if (selectedIndex >= 0) buildingByIndex.get(selectedIndex)?.classList.remove('is-selected');
    selectedIndex = index;
    const day = days[index];
    const group = buildingByIndex.get(index);
    if (!day || !group) {
      selectionText.textContent = 'Choose a building to see its date and contribution count.';
      return;
    }
    group.classList.add('is-selected');
    selectionText.textContent = `${dateLabel(day.date, true)} · ${number.format(day.count)} ${day.count === 1 ? 'contribution' : 'contributions'}. This is a daily total, not a list of individual commits.`;
  }

  function updateIndex(nextIndex) {
    const bounded = Math.max(0, Math.min(days.length - 1, Number(nextIndex)));
    if (!Number.isInteger(bounded)) return;

    if (currentIndex >= 0 && bounded !== currentIndex) {
      const lower = Math.min(currentIndex, bounded) + 1;
      const upper = Math.max(currentIndex, bounded);
      for (let index = lower; index <= upper; index += 1) {
        const building = buildingByIndex.get(index);
        if (building) building.classList.toggle('is-future', index > bounded);
      }
    } else if (currentIndex < 0) {
      buildings.forEach((building) => {
        building.classList.toggle('is-future', Number(building.dataset.index) > bounded);
      });
    }

    currentIndex = bounded;
    range.value = String(bounded);
    const day = days[bounded];
    const stats = prefixes[bounded];
    dateOutput.textContent = dateLabel(day.date);
    totalMetric.textContent = number.format(stats.total);
    activeMetric.textContent = number.format(stats.active);
    currentStreakMetric.textContent = number.format(stats.currentStreak);
    longestStreakMetric.textContent = number.format(stats.longestStreak);
    if (selectedIndex > bounded) updateSelection(-1);
  }

  function pausePlayback() {
    if (playTimer !== null) window.clearInterval(playTimer);
    playTimer = null;
    playButton.setAttribute('aria-pressed', 'false');
  }

  function playPlayback() {
    if (!days.length || playTimer !== null) return;
    if (currentIndex >= days.length - 1) updateIndex(0);
    playButton.setAttribute('aria-pressed', 'true');
    playTimer = window.setInterval(() => {
      if (currentIndex >= days.length - 1) {
        pausePlayback();
        status.textContent = 'Playback complete · use Restart to replay the year.';
        return;
      }
      updateIndex(currentIndex + 1);
    }, 140);
  }

  function updateExpandedState() {
    const expanded = fallbackExpanded || document.fullscreenElement === explorer;
    closeButton.hidden = !expanded;
    expandButton.hidden = expanded;
    if (!expanded) explorer.classList.remove('is-expanded');
  }

  async function openExpanded() {
    explorer.classList.add('is-expanded');
    closeButton.hidden = false;
    expandButton.hidden = true;
    fallbackExpanded = true;
    if (typeof explorer.requestFullscreen === 'function') {
      try {
        await explorer.requestFullscreen();
      } catch (_) {
        fallbackExpanded = true;
      }
    }
    updateExpandedState();
    closeButton.focus();
  }

  async function closeExpanded() {
    const wasExpanded = fallbackExpanded || document.fullscreenElement === explorer;
    fallbackExpanded = false;
    if (document.fullscreenElement === explorer && document.exitFullscreen) {
      try {
        await document.exitFullscreen();
      } catch (_) {
        // The overlay class below remains a reliable close fallback.
      }
    }
    explorer.classList.remove('is-expanded');
    updateExpandedState();
    if (wasExpanded) expandButton.focus();
  }

  function showFallback(error) {
    status.textContent = 'Live data is temporarily unavailable.';
    explorer.querySelector('[data-city-error]').textContent = error;
    fallback.hidden = false;
  }

  async function load() {
    try {
      const sourceUrl = explorer.dataset.sourceUrl;
      const response = await fetch(sourceUrl, { cache: 'no-cache' });
      if (!response.ok) throw new Error(`GitHub returned ${response.status}.`);
      const payload = await response.json();
      days = validatePayload(payload);
      buildStats();
      buildCity();

      range.max = String(days.length - 1);
      range.disabled = false;
      [playButton, pauseButton, restartButton, expandButton].forEach((button) => { button.disabled = false; });
      startLabel.textContent = dateLabel(days[0].date);
      endLabel.textContent = dateLabel(days[days.length - 1].date);
      status.textContent = `Public calendar · ${number.format(days.length)} dates`;
      updateIndex(days.length - 1);
    } catch (error) {
      showFallback(error instanceof Error ? error.message : 'The contribution data could not be loaded.');
    }
  }

  range.addEventListener('input', () => updateIndex(range.value));
  playButton.addEventListener('click', playPlayback);
  pauseButton.addEventListener('click', pausePlayback);
  restartButton.addEventListener('click', () => {
    pausePlayback();
    updateIndex(0);
    status.textContent = 'Timeline reset to the first calendar date.';
  });
  expandButton.addEventListener('click', openExpanded);
  closeButton.addEventListener('click', closeExpanded);
  document.addEventListener('fullscreenchange', updateExpandedState);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && fallbackExpanded && document.fullscreenElement !== explorer) closeExpanded();
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) pausePlayback();
  });
  window.addEventListener('pagehide', pausePlayback, { once: true });

  buildingsLayer.addEventListener('pointerover', (event) => {
    const building = event.target.closest('[data-city-building]');
    if (building && buildingsLayer.contains(building)) updateSelection(Number(building.dataset.index));
  });
  buildingsLayer.addEventListener('focusin', (event) => {
    const building = event.target.closest('[data-city-building]');
    if (building) updateSelection(Number(building.dataset.index));
  });
  buildingsLayer.addEventListener('click', (event) => {
    const building = event.target.closest('[data-city-building]');
    if (building) updateSelection(Number(building.dataset.index));
  });
  buildingsLayer.addEventListener('keydown', (event) => {
    const current = event.target.closest('[data-city-building]');
    if (!current) return;
    const visibleBuildings = buildings.filter((building) => !building.classList.contains('is-future'));
    const visibleIndex = visibleBuildings.indexOf(current);
    let next = -1;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = Math.min(visibleBuildings.length - 1, visibleIndex + 1);
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = Math.max(0, visibleIndex - 1);
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = visibleBuildings.length - 1;
    if (next >= 0) {
      event.preventDefault();
      current.setAttribute('tabindex', '-1');
      visibleBuildings[next].setAttribute('tabindex', '0');
      visibleBuildings[next].focus();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      updateSelection(Number(current.dataset.index));
    }
  });

  load();
})();
