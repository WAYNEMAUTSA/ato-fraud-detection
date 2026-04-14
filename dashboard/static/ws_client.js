/* ATO Shield v2 - WebSocket Client for Real-time Updates */

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;
let volumeChart = null;
let fraudTypeChart = null;

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws?analyst_id=demo`;

  try {
    ws = new WebSocket(wsUrl);
  } catch (error) {
    console.warn('⚠️ WebSocket connection failed, live updates disabled:', error.message);
    updateConnectionStatus('error');
    return;
  }

  ws.onopen = function() {
    console.log('✅ WebSocket connected');
    reconnectAttempts = 0;
    updateConnectionStatus('connected');
  };

  ws.onmessage = function(event) {
    try {
      const data = JSON.parse(event.data);
      handleWSMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onclose = function() {
    console.log('❌ WebSocket disconnected');
    updateConnectionStatus('disconnected');
    attemptReconnect();
  };

  ws.onerror = function(error) {
    console.warn('⚠️ WebSocket error (live updates unavailable):', error);
  };
}

function handleWSMessage(data) {
  if (data.type === 'new_case') {
    handleNewCaseAlert(data);
  } else if (data.type === 'stats_update') {
    handleStatsUpdate(data.data);
  } else if (data.type === 'connected') {
    console.log('✅ WebSocket session established for:', data.analyst_id);
    updateConnectionStatus('connected');
  } else if (data.type === 'ping') {
    // Respond to server heartbeat
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send('pong');
    }
  }
}

function handleStatsUpdate(stats) {
  console.log('📊 Stats update received:', stats);

  // Update open cases count
  const openCasesElements = document.querySelectorAll('[data-stat="open_cases"]');
  openCasesElements.forEach(el => {
    el.textContent = stats.open_cases;
  });

  // Update screened count
  const screenedElements = document.querySelectorAll('[data-stat="screened_count"]');
  screenedElements.forEach(el => {
    el.textContent = stats.screened_count;
  });

  // Update protected value
  const protectedValueElements = document.querySelectorAll('[data-stat="protected_value"]');
  protectedValueElements.forEach(el => {
    el.textContent = `₹${stats.protected_value}`;
  });

  // Update threat level indicator
  const threatLabel = document.querySelector('[data-stat="threat_label"]');
  if (threatLabel) {
    threatLabel.textContent = stats.threat_label;
    threatLabel.style.color = stats.threat_color;
  }

  const threatDot = document.querySelector('.threat-dot');
  if (threatDot) {
    threatDot.className = `threat-dot ${stats.threat_level}`;
  }

  const threatIndicator = document.querySelector('.threat-indicator');
  if (threatIndicator) {
    threatIndicator.style.borderLeftColor = stats.threat_color;
  }

  // Update threat sub text
  const threatSub = document.querySelector('[data-stat="threat_sub"]');
  if (threatSub) {
    threatSub.textContent = `${stats.open_cases} cases require attention`;
  }

  // Update queue badge
  const queueBadge = document.getElementById('queue-badge');
  if (queueBadge) {
    queueBadge.textContent = stats.open_cases;
  }

  // Update charts if they exist
  if (stats.volume_legit && stats.volume_flagged && volumeChart) {
    volumeChart.data.datasets[0].data = stats.volume_legit;
    volumeChart.data.datasets[1].data = stats.volume_flagged;
    volumeChart.update('none'); // Update without animation for smooth transition
  }

  if (stats.fraud_type_data && fraudTypeChart) {
    fraudTypeChart.data.datasets[0].data = stats.fraud_type_data;
    fraudTypeChart.update('none');
  }

  // Show toast for significant changes
  if (stats.open_cases === 0) {
    showToast('🛡 All cases resolved - queue is clear!', 'success');
  }

  // Update profile stats if elements exist (on any page with profile modal)
  updateProfileStats();
}

// Periodic stats polling as fallback (every 5 seconds)
async function pollDashboardStats() {
  try {
    const response = await fetch('/api/v1/dashboard/stats');
    if (response.ok) {
      const stats = await response.json();
      handleStatsUpdate(stats);
    }
  } catch (error) {
    console.warn('⚠️ Stats polling failed:', error);
  }
}

// Start polling when page loads
setInterval(pollDashboardStats, 5000);

function handleNewCaseAlert(alertData) {
  console.log('🚨 New case alert:', alertData);

  // Show toast notification
  showToast(
    `⚠ New ${alertData.risk_level} risk case — ${alertData.customer_name || 'Unknown'}`,
    'warning'
  );

  // Update queue badge if on queue page
  const queueBadge = document.getElementById('queue-badge');
  if (queueBadge) {
    const currentCount = parseInt(queueBadge.textContent) || 0;
    queueBadge.textContent = currentCount + 1;
  }

  // If on alert queue page, prepend new case card
  const caseList = document.getElementById('case-list');
  if (caseList) {
    const newCard = createCaseCard(alertData, true);
    caseList.insertBefore(newCard, caseList.firstChild);
  }
}

function attemptReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.log('⚠️ Max reconnection attempts reached');
    return;
  }
  
  reconnectAttempts++;
  console.log(`🔄 Reconnecting... (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
  
  setTimeout(() => {
    connectWebSocket();
  }, RECONNECT_DELAY);
}

function updateConnectionStatus(status) {
  const statusEl = document.getElementById('ws-status');
  if (statusEl) {
    if (status === 'connected') {
      statusEl.style.display = 'none';
    } else if (status === 'error') {
      statusEl.style.display = 'block';
      statusEl.style.background = 'var(--risk-medium-bg)';
      statusEl.style.color = 'var(--risk-medium)';
      statusEl.textContent = '⚠ Live updates unavailable — using static mode';
    } else {
      statusEl.style.display = 'block';
      statusEl.textContent = '⚠ Live updates paused — reconnecting...';
    }
  }
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function createCaseCard(caseData, isNew = false) {
  const card = document.createElement('div');
  const riskLevel = (caseData.risk_level || 'LOW').toLowerCase();
  card.className = `case-card case-${riskLevel}`;
  if (isNew) {
    card.style.animation = 'slideIn 0.3s ease';
  }

  const riskBadge = `<span class="badge badge-${riskLevel}">${caseData.risk_level || 'LOW'}</span>`;
  const fraudType = (caseData.fraud_type || '').toUpperCase();
  const fraudTag = fraudType ? `<span class="fraud-tag fraud-${fraudType.toLowerCase()}">${fraudType}</span>` : '';
  const amount = caseData.amount ? `₹${caseData.amount.toLocaleString()}` : '';

  card.innerHTML = `
    <div class="case-left">
      ${riskBadge}
      ${fraudTag}
    </div>
    <div class="case-middle">
      <div class="case-name">${caseData.customer_name || 'Unknown'}</div>
      <div class="case-amount">${amount}</div>
      <div class="case-reason">${caseData.reason_summary || ''}</div>
    </div>
    <div class="case-right">
      <span class="case-time">${caseData.minutes_ago || 0} min ago</span>
      <a href="/case/${caseData.case_id}" class="case-review">Review →</a>
    </div>
  `;

  card.onclick = () => {
    window.location.href = `/case/${caseData.case_id}`;
  };

  return card;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  connectWebSocket();
  loadSettings();
  updateProfileStats();
});

// Settings Modal Functions
function openSettingsModal() {
  document.getElementById('settings-modal').style.display = 'block';
}

function closeSettingsModal() {
  document.getElementById('settings-modal').style.display = 'none';
}

function saveSettings() {
  const settings = {
    refreshInterval: document.getElementById('refresh-interval').value,
    defaultSort: document.getElementById('default-sort').value,
    toastNotifications: document.getElementById('toast-notifications').checked,
    soundAlerts: document.getElementById('sound-alerts').checked,
    compactMode: document.getElementById('compact-mode').checked,
    chartAnimation: document.getElementById('chart-animation').value,
    apiKey: document.getElementById('api-key-input').value,
    webhookUrl: document.getElementById('webhook-url').value
  };

  localStorage.setItem('ato_shield_settings', JSON.stringify(settings));
  showToast('✓ Settings saved successfully', 'success');
  closeSettingsModal();

  // Apply settings
  applySettings(settings);
}

function resetSettings() {
  const defaults = {
    refreshInterval: '5000',
    defaultSort: 'oldest',
    toastNotifications: true,
    soundAlerts: false,
    compactMode: false,
    chartAnimation: 'smooth',
    apiKey: 'ask_live_demo_key_12345',
    webhookUrl: ''
  };

  localStorage.setItem('ato_shield_settings', JSON.stringify(defaults));
  loadSettings();
  showToast('✓ Settings reset to defaults', 'success');
}

function loadSettings() {
  const saved = localStorage.getItem('ato_shield_settings');
  if (saved) {
    try {
      const settings = JSON.parse(saved);
      document.getElementById('refresh-interval').value = settings.refreshInterval || '5000';
      document.getElementById('default-sort').value = settings.defaultSort || 'oldest';
      document.getElementById('toast-notifications').checked = settings.toastNotifications !== false;
      document.getElementById('sound-alerts').checked = settings.soundAlerts || false;
      document.getElementById('compact-mode').checked = settings.compactMode || false;
      document.getElementById('chart-animation').value = settings.chartAnimation || 'smooth';
      document.getElementById('api-key-input').value = settings.apiKey || 'ask_live_demo_key_12345';
      document.getElementById('webhook-url').value = settings.webhookUrl || '';

      applySettings(settings);
    } catch (error) {
      console.warn('⚠️ Failed to load settings:', error);
    }
  }
}

function applySettings(settings) {
  // Apply compact mode
  if (settings.compactMode) {
    document.body.classList.add('compact-mode');
  } else {
    document.body.classList.remove('compact-mode');
  }
}

// Profile Modal Functions
function openProfileModal() {
  document.getElementById('profile-modal').style.display = 'block';
  updateProfileStats();
}

function closeProfileModal() {
  document.getElementById('profile-modal').style.display = 'none';
}

function updateProfileStats() {
  // Fetch analyst stats from API
  fetch('/api/v1/dashboard/stats')
    .then(response => response.json())
    .then(data => {
      // Update cases reviewed
      const casesReviewedEl = document.getElementById('profile-cases-reviewed');
      if (casesReviewedEl) {
        casesReviewedEl.textContent = data.analyst_cases_reviewed || 0;
      }

      // Update accuracy rate (add % sign)
      const accuracyEl = document.getElementById('profile-accuracy');
      if (accuracyEl) {
        accuracyEl.textContent = (data.analyst_accuracy || 0) + '%';
      }

      // Update average review time (format as minutes)
      const avgTimeEl = document.getElementById('profile-avg-time');
      if (avgTimeEl) {
        const avgTime = data.analyst_avg_time || 0;
        avgTimeEl.textContent = avgTime + 'm';
      }

      // Update decision breakdown
      const blockedEl = document.getElementById('profile-blocked');
      if (blockedEl) {
        blockedEl.textContent = data.analyst_blocked || 0;
      }

      const frozenEl = document.getElementById('profile-frozen');
      if (frozenEl) {
        frozenEl.textContent = data.analyst_frozen || 0;
      }

      const escalatedEl = document.getElementById('profile-escalated');
      if (escalatedEl) {
        escalatedEl.textContent = data.analyst_escalated || 0;
      }

      const clearedEl = document.getElementById('profile-cleared');
      if (clearedEl) {
        clearedEl.textContent = data.analyst_cleared || 0;
      }

      // Update recent activity list
      const activityContainer = document.getElementById('profile-recent-activity');
      if (activityContainer) {
        const activities = data.analyst_recent_activity || [];
        if (activities.length === 0) {
          activityContainer.innerHTML = '<div class="empty-state"><p>No recent activity</p></div>';
        } else {
          activityContainer.innerHTML = activities.map(activity => {
            const actionClass = getActionClass(activity.action);
            const timeAgo = formatTimestamp(activity.timestamp);
            return `
              <div class="activity-item">
                <span class="badge ${actionClass}">${activity.action}</span>
                <span class="activity-case-id">${activity.case_id.substring(0, 8)}...</span>
                <span class="activity-time">${timeAgo}</span>
              </div>
            `;
          }).join('');
        }
      }
    })
    .catch(error => {
      console.warn('⚠️ Failed to update profile stats:', error);
    });
}

function getActionClass(action) {
  switch (action) {
    case 'BLOCK': return 'badge-risk';
    case 'FREEZE': return 'badge-warning';
    case 'ESCALATE': return 'badge-info';
    case 'CLEAR': return 'badge-success';
    default: return 'badge-default';
  }
}

function formatTimestamp(isoString) {
  if (!isoString) return 'Unknown';
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return diffMins + 'm ago';
    if (diffHours < 24) return diffHours + 'h ago';
    return diffDays + 'd ago';
  } catch (e) {
    return 'Unknown';
  }
}

function signOut() {
  if (confirm('Are you sure you want to sign out?')) {
    showToast('✓ Signed out successfully', 'success');
    // In a real app, this would redirect to login page
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 1000);
  }
}

// Close modals on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeSettingsModal();
    closeProfileModal();
  }
});
