// scripts/sidebar.js

document.addEventListener('DOMContentLoaded', () => {
  const navLinks = document.querySelectorAll('.nav-item a');

  function createPlaceholder(title) {
    const div = document.createElement('div');
    div.className = 'placeholder-view';
    div.style.padding = '40px 20px';
    div.style.color = '#e0e0e0';
    div.style.fontFamily = 'var(--font-montserrat)';
    div.style.fontSize = '1.2em';
    div.style.textAlign = 'center';
    div.style.display = 'flex';
    div.style.flexDirection = 'column';
    div.style.justifyContent = 'center';
    div.style.alignItems = 'center';
    div.style.height = '100%';
    div.innerHTML = `
      <div style="font-size: 3em; margin-bottom: 20px;">🚧</div>
      <h2 style="margin: 0 0 16px; font-weight: 600; color: #1e90ff;">${title}</h2>
      <p style="margin: 0; color: #aaa; max-width: 500px; line-height: 1.5;">
        This page is under construction.<br>
        Stay tuned for updates!
      </p>
    `;
    return div;
  }

  function showView(viewName, title) {
    // Hide all views
    document.querySelectorAll('.view-container').forEach(view => {
      view.classList.remove('active');
    });

    // Show correct view
    if (viewName === 'kanban') {
      document.getElementById('kanban-view')?.classList.add('active');
    } else if (viewName === 'code') {
      document.getElementById('kan8-view')?.classList.add('active');
    }

    // Handle placeholders
    const leftColumn = document.querySelector('.left-column');
    const existingPlaceholder = leftColumn.querySelector('.placeholder-view');
    if (existingPlaceholder) existingPlaceholder.remove();

    if (!['kanban', 'code'].includes(viewName)) {
      const cleanTitle = title || viewName.charAt(0).toUpperCase() + viewName.slice(1);
      leftColumn.appendChild(createPlaceholder(cleanTitle));
    }
  }

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();

      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
      });

      const navItem = link.closest('.nav-item');
      if (navItem) navItem.classList.add('active');

      const text = link.textContent.trim();
      let view = 'kanban';
      let title = '';

      if (text.includes('Kanban board')) {
        view = 'kanban';
      } else if (text.includes('Code')) {
        view = 'code';
      } else if (text.includes('Timeline')) {
        view = 'timeline';
        title = 'Timeline';
      } else if (text.includes('Reports')) {
        view = 'reports';
        title = 'Reports';
      } else {
        title = text
          .replace(/[\u{1F600}-\u{1F6FF}\u{1F300}-\u{1F5FF}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
          .replace(/\s*\([^)]*\)/g, '')
          .replace(/\s*BETA\s*/gi, '')
          .replace(/\s+/g, ' ')
          .trim();
      }

      showView(view, title);
    });
  });

  showView('kanban', '');

  // Sidebar collapse
  const sidebar = document.querySelector('.kanban-sidebar');
  const toggleBtn = document.querySelector('.sidebar-toggle');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed');
      
      const icon = toggleBtn.querySelector('i');
      if (sidebar.classList.contains('collapsed')) {
        icon.className = 'fas fa-chevron-right';
      } else {
        icon.className = 'fas fa-chevron-left';
      }
    });
  }
});