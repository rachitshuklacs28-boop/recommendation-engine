/**
 * static/js/dashboard.js
 * ------------------------
 * Loaded on both index.html and dashboard.html. On the dashboard page
 * (detected via the `data-user-id` attribute on <body>), it fetches the
 * profile and live recommendations from the Flask API and renders them.
 */

document.addEventListener('DOMContentLoaded', () => {
  const userId = document.body.dataset.userId;
  if (!userId) return; // not the dashboard page — nothing to do here

  loadProfile(userId);
  loadRecommendations(userId);
  setupTabs();
});

function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      document.querySelectorAll('.results-panel').forEach((p) => p.classList.remove('active'));

      tab.classList.add('active');
      document.getElementById(`panel-${tab.dataset.target}`).classList.add('active');
    });
  });
}

async function loadProfile(userId) {
  try {
    const res = await fetch(`/api/profile/${userId}`);
    if (!res.ok) throw new Error('Profile not found');
    const user = await res.json();

    document.getElementById('profile-name').textContent = user.name;
    document.getElementById('profile-education').textContent = user.education;
    document.getElementById('profile-level').textContent = user.experience_level;
    document.getElementById('profile-goal').textContent = user.career_goal;

    renderTags('profile-skills', user.skills);
    renderTags('profile-interests', user.interests);

    document.getElementById('profile-loading').hidden = true;
    document.getElementById('profile-content').hidden = false;
  } catch (err) {
    document.getElementById('profile-loading').textContent = 'Could not load profile.';
  }
}

function renderTags(containerId, semicolonSeparated) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  (semicolonSeparated || '')
    .split(';')
    .map((s) => s.trim())
    .filter(Boolean)
    .forEach((item) => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = item;
      container.appendChild(tag);
    });
}

async function loadRecommendations(userId) {
  try {
    const res = await fetch(`/api/recommendations/${userId}?top_n=6`);
    if (!res.ok) throw new Error('Could not compute recommendations');
    const data = await res.json();

    renderCategory('internship', data.recommendations.internship, {
      subtitle: (item) => `${item.company} · ${item.domain} · ${item.mode}`,
      meta: (item) => [
        item.duration ? `⏱ ${item.duration}` : null,
        item.location ? `📍 ${item.location}` : null,
        `Level: ${item.level}`,
      ],
    });

    renderCategory('project', data.recommendations.project, {
      subtitle: (item) => `${item.domain} · ${item.category}`,
      meta: (item) => [`Difficulty: ${item.difficulty_level}`],
    });

    renderCategory('learning_resource', data.recommendations.learning_resource, {
      subtitle: (item) => `${item.provider} · ${item.resource_type}`,
      meta: (item) => [
        `Level: ${item.level}`,
        item.url ? { link: item.url, label: 'Open resource ↗' } : null,
      ],
    });

    document.getElementById('results-loading').hidden = true;
    document.getElementById('results-content').hidden = false;
  } catch (err) {
    document.getElementById('results-loading').textContent = 'Could not compute recommendations. Please try again.';
  }
}

function scoreTier(score) {
  if (score >= 60) return 'tier-high';
  if (score >= 35) return 'tier-mid';
  return 'tier-low';
}

function renderCategory(key, items, { subtitle, meta }) {
  const panel = document.getElementById(`panel-${key}`);
  panel.innerHTML = '';

  if (!items || items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'No strong matches yet — try adding more skills to your profile.';
    panel.appendChild(empty);
    return;
  }

  const template = document.getElementById('card-template');

  items.forEach((item) => {
    const card = template.content.cloneNode(true);

    card.querySelector('.rec-title').textContent = item.title;
    card.querySelector('.rec-subtitle').textContent = subtitle(item);

    const meterWrap = card.querySelector('.match-meter');
    meterWrap.classList.add(scoreTier(item.match_score));
    card.querySelector('.match-score').textContent = `${item.match_score}%`;
    card.querySelector('.match-bar-fill').style.width = `${Math.min(item.match_score, 100)}%`;

    card.querySelector('.rec-explanation').textContent = item.explanation;

    const tagsWrap = card.querySelector('.rec-tags');
    (item.matched_skills || []).forEach((skill) => {
      const tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = skill;
      tagsWrap.appendChild(tag);
    });

    const breakdownWrap = card.querySelector('.rec-breakdown');
    const breakdown = item.score_breakdown || {};
    const labels = {
      content_similarity: 'Content Sim.',
      skill_match: 'Skill Match',
      goal_alignment: 'Goal Fit',
      experience_fit: 'Exp. Fit',
    };
    Object.entries(labels).forEach(([field, label]) => {
      const wrap = document.createElement('div');
      wrap.className = 'breakdown-item';
      wrap.innerHTML = `<span class="breakdown-label">${label}</span><span class="breakdown-value">${breakdown[field] ?? 0}%</span>`;
      breakdownWrap.appendChild(wrap);
    });

    const metaWrap = card.querySelector('.rec-meta');
    meta(item).filter(Boolean).forEach((entry) => {
      if (typeof entry === 'string') {
        const span = document.createElement('span');
        span.textContent = entry;
        metaWrap.appendChild(span);
      } else if (entry.link) {
        const a = document.createElement('a');
        a.href = entry.link;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = entry.label;
        metaWrap.appendChild(a);
      }
    });

    panel.appendChild(card);
  });
}
