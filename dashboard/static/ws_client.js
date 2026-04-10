/* ATO Shield v2 - WebSocket Client for Real-time Alerts */

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws?analyst_id=demo`;
  
  console.log('🔌 Connecting to WebSocket...');
  
  ws = new WebSocket(wsUrl);
  
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
    console.error('WebSocket error:', error);
  };
}

function handleWSMessage(data) {
  if (data.type === 'new_case') {
    handleNewCaseAlert(data);
  }
}

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
  card.className = `case-card case-${caseData.risk_level.toLowerCase()}`;
  if (isNew) {
    card.style.animation = 'slideIn 0.3s ease';
  }
  
  const riskBadge = `<span class="badge badge-${caseData.risk_level.toLowerCase()}">${caseData.risk_level}</span>`;
  const fraudTag = caseData.fraud_type ? `<span class="fraud-tag fraud-${caseData.fraud_type.toLowerCase()}">${caseData.fraud_type}</span>` : '';
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
});
