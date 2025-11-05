// scripts/sidebar.js

document.addEventListener('DOMContentLoaded', () => {
  // Select all nav links in the sidebar
  const navLinks = document.querySelectorAll('.sidebar-nav a');

  // Main content areas we'll toggle
  const kanbanBoard = document.querySelector('.kanban-board');
  const mainContentWrapper = document.querySelector('.main-content-wrapper');

  // Optional: Create placeholder containers for other views
  let timelineView = null;
  let reportsView = null;

  // Helper: Create a placeholder view
  function createPlaceholder(title) {
    const div = document.createElement('div');
    div.className = 'placeholder-view';
    div.style.padding = '20px';
    div.style.color = '#f0f0f0';
    div.style.fontFamily = 'var(--font-montserrat)';
    div.innerHTML = `<h2>${title}</h2><p>This view is under construction.</p>`;
    return div;
  }

  // Hide all views except the one we want
  function showView(viewToShow) {
    // Hide Kanban board if not needed
    if (kanbanBoard) {
      kanbanBoard.style.display = viewToShow === 'kanban' ? 'flex' : 'none';
    }

    // Remove any existing placeholder
    const existingPlaceholder = mainContentWrapper.querySelector('.placeholder-view');
    if (existingPlaceholder) {
      existingPlaceholder.remove();
    }

    // Show placeholder if needed
    if (viewToShow === 'timeline') {
      timelineView = timelineView || createPlaceholder('Timeline View');
      mainContentWrapper.prepend(timelineView);
    } else if (viewToShow === 'reports') {
      reportsView = reportsView || createPlaceholder('Reports View');
      mainContentWrapper.prepend(reportsView);
    }
  }

  // Add click handlers
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();

      // Remove 'active' class from all items
      document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
      });

      // Add 'active' to clicked parent .nav-item
      const navItem = link.closest('.nav-item');
      if (navItem) navItem.classList.add('active');

      // Determine which view to show
      let view = 'kanban'; // default

      const text = link.textContent.trim();
      if (text.includes('Timeline')) {
        view = 'timeline';
      } else if (text.includes('Reports')) {
        view = 'reports';
      } else if (text.includes('Kanban board')) {
        view = 'kanban';
      }

      // Update UI
      showView(view);
    });
  });

  // Initialize: show Kanban by default
  showView('kanban');
});