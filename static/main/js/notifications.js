// In-app Notifications System for CreditCampus (DEPT)

document.addEventListener('DOMContentLoaded', () => {
  const trigger = document.querySelector('.notification-trigger');
  const dropdown = document.querySelector('.notification-dropdown');
  const badge = document.getElementById('notification-badge');
  const listContainer = document.getElementById('notification-list');
  const markAllBtn = document.getElementById('mark-all-read-btn');

  if (!trigger || !dropdown) return;

  // Initialize and load notifications
  fetchNotifications();

  // Poll for new notifications every 60 seconds to optimize server load
  setInterval(fetchNotifications, 60000);

  // Toggle dropdown on click
  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    const menu = trigger.parentElement;
    menu.classList.toggle('active');
    
    // Position adjustments if needed
    if (menu.classList.contains('active')) {
      fetchNotifications();
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
      trigger.parentElement.classList.remove('active');
    }
  });

  // Mark all as read click event
  if (markAllBtn) {
    markAllBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      markAllNotificationsAsRead();
    });
  }

  // Helper: Get CSRF Token (with fallback)
  function getCsrfToken() {
    // Primary: hidden input inside notification-menu container
    const csrfInput = document.querySelector('.notification-menu input[name=csrfmiddlewaretoken]');
    if (csrfInput && csrfInput.value) {
      return csrfInput.value;
    }
    // Fallback 1: global csrfToken variable (defined in matching.html)
    if (typeof csrfToken !== 'undefined') {
      return csrfToken;
    }
    // Fallback 2: hidden form input (defined in profile.html)
    const generalInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (generalInput && generalInput.value) {
      return generalInput.value;
    }
    return '';
  }

  // Fetch notifications list from API
  function fetchNotifications() {
    fetch('/aimatch/api/notifications')
      .then(res => {
        if (res.status === 401) {
          // Logged out
          return;
        }
        return res.json();
      })
      .then(data => {
        if (!data) return;
        updateBadge(data.unread_count);
        renderNotifications(data.notifications);
      })
      .catch(err => console.error("Error fetching notifications:", err));
  }

  // Update unread count badge
  function updateBadge(count) {
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }

  // Format timestamp relatively (e.g. "3분 전", "1시간 전", "어제")
  function formatRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays === 1) return '어제';
    if (diffDays < 7) return `${diffDays}일 전`;
    
    // Absolute date formatting
    return `${date.getMonth() + 1}월 ${date.getDate()}일`;
  }

  // Render notification elements
  function renderNotifications(notifications) {
    if (!listContainer) return;
    listContainer.innerHTML = '';

    if (notifications.length === 0) {
      listContainer.innerHTML = '<div class="notification-empty">새로운 알림이 없습니다.</div>';
      return;
    }

    notifications.forEach(n => {
      const item = document.createElement('div');
      item.className = `notification-item ${n.is_read ? '' : 'unread'}`;
      item.dataset.id = n.id;
      
      item.innerHTML = `
        <div class="notification-text">${escapeHtml(n.message)}</div>
        <div class="notification-time">${formatRelativeTime(n.created_at)}</div>
      `;

      item.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!n.is_read) {
          markSingleNotificationAsRead(n.id, item);
        }
      });

      listContainer.appendChild(item);
    });
  }

  // Escape HTML helper to prevent XSS
  function escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
  }

  // Mark all notifications as read
  function markAllNotificationsAsRead() {
    const csrftoken = getCsrfToken();
    fetch('/aimatch/api/notifications/read', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        updateBadge(0);
        fetchNotifications();
      }
    })
    .catch(err => console.error("Error marking all read:", err));
  }

  // Mark a single notification as read
  function markSingleNotificationAsRead(id, element) {
    const csrftoken = getCsrfToken();
    fetch('/aimatch/api/notifications/read', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ notification_id: id })
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        element.classList.remove('unread');
        // Re-fetch count
        fetchNotifications();
      }
    })
    .catch(err => console.error("Error marking notification read:", err));
  }
});
