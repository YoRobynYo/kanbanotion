// scripts/kan8.js
document.addEventListener('DOMContentLoaded', () => {
  const kan8Cards = document.getElementById('kan8Cards');
  const kan8Connections = document.getElementById('kan8Connections');
  const addCardBtn = document.getElementById('kan8-add-card');
  
  if (!kan8Cards || !kan8Connections) return;

  let cardId = 1;
  let connections = []; // Store connection data
  let isConnecting = false;
  let startCard = null;
  let startPoint = null;

  // Create connection line in SVG
  function createConnectionLine(x1, y1, x2, y2) {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('stroke', '#667eea');
    line.setAttribute('stroke-width', '2');
    line.setAttribute('marker-end', 'url(#arrowhead)');
    return line;
  }

  // Update all connection lines
  function updateConnections() {
    // Clear SVG
    while (kan8Connections.firstChild) {
      kan8Connections.removeChild(kan8Connections.firstChild);
    }
    
    // Redraw all connections
    connections.forEach(conn => {
      const from = document.querySelector(`[data-card-id="${conn.from}"]`);
      const to = document.querySelector(`[data-card-id="${conn.to}"]`);
      
      if (from && to) {
        const fromRect = from.getBoundingClientRect();
        const toRect = to.getBoundingClientRect();
        const containerRect = kan8Cards.getBoundingClientRect();
        
        // Get center points
        const x1 = fromRect.left + fromRect.width/2 - containerRect.left;
        const y1 = fromRect.top + fromRect.height/2 - containerRect.top;
        const x2 = toRect.left + toRect.width/2 - containerRect.left;
        const y2 = toRect.top + toRect.height/2 - containerRect.top;
        
        const line = createConnectionLine(x1, y1, x2, y2);
        kan8Connections.appendChild(line);
      }
    });
  }

  // Create a card
  function createCard(title, tech, desc, icon, x = 100, y = 100) {
    const card = document.createElement('div');
    card.className = 'kan8-card';
    card.dataset.cardId = `card-${cardId++}`;
    card.style.left = `${x}px`;
    card.style.top = `${y}px`;
    
    card.innerHTML = `
      <div class="kan8-card-header">
        <span class="kan8-card-icon">${icon}</span>
        <span class="kan8-card-title">${title}</span>
      </div>
      <div class="kan8-card-body">
        <span class="kan8-card-tech">${tech}</span>
        <p class="kan8-card-desc">${desc}</p>
      </div>
      <div class="kan8-card-actions">
        <i class="fas fa-pen" title="Edit"></i>
        <i class="fas fa-link" title="Connect"></i>
        <i class="fas fa-trash" title="Delete"></i>
      </div>
      <div class="kan8-connection-point top"></div>
      <div class="kan8-connection-point right"></div>
      <div class="kan8-connection-point bottom"></div>
      <div class="kan8-connection-point left"></div>
    `;
    
    // Handle card dragging
    card.addEventListener('mousedown', (e) => {
      if (e.target.closest('.kan8-card-actions')) return;
      
      const startX = e.clientX - card.offsetLeft;
      const startY = e.clientY - card.offsetTop;
      
      const move = (e) => {
        card.style.left = `${e.clientX - startX}px`;
        card.style.top = `${e.clientY - startY}px`;
        updateConnections(); // Update lines while dragging
      };
      
      const stop = () => {
        document.removeEventListener('mousemove', move);
        document.removeEventListener('mouseup', stop);
      };
      
      document.addEventListener('mousemove', move);
      document.addEventListener('mouseup', stop);
    });
    
    // Handle connection mode
    card.addEventListener('click', (e) => {
      if (!isConnecting) return;
      e.stopPropagation();
      
      const targetCardId = card.dataset.cardId;
      
      if (startCard !== targetCardId) {
        connections.push({ from: startCard, to: targetCardId });
        updateConnections();
      }
      
      isConnecting = false;
      startCard = null;
      startPoint = null;
      
      // Reset all cards to normal state
      document.querySelectorAll('.kan8-card').forEach(c => {
        c.style.boxShadow = '';
      });
    });
    
    return card;
  }

  // Initialize with sample cards
  function initKan8() {
    if (kan8Cards.children.length > 0) return;
    
    kan8Cards.appendChild(createCard('Login.jsx', 'React Component', 'User authentication form', '⚛️', 100, 100));
    kan8Cards.appendChild(createCard('AuthAPI', 'Node.js / Express', 'Authentication endpoint', '🟢', 450, 100));
    kan8Cards.appendChild(createCard('User DB', 'PostgreSQL', 'User credentials table', '🗄️', 800, 100));
    
    // Add a sample connection
    connections.push({ from: 'card-1', to: 'card-2' });
    connections.push({ from: 'card-2', to: 'card-3' });
    updateConnections();
  }

  // Add card button
  if (addCardBtn) {
    addCardBtn.addEventListener('click', () => {
      const x = 100 + Math.random() * 200;
      const y = 200 + Math.random() * 200;
      kan8Cards.appendChild(createCard('New File.js', 'JavaScript', 'Click to edit', '📄', x, y));
    });
  }

  // Start connection mode
  document.addEventListener('click', (e) => {
    if (e.target.closest('.fa-link')) {
      e.stopPropagation();
      const card = e.target.closest('.kan8-card');
      const cardId = card.dataset.cardId;
      
      isConnecting = true;
      startCard = cardId;
      
      // Highlight all cards as connectable
      document.querySelectorAll('.kan8-card').forEach(c => {
        if (c.dataset.cardId !== cardId) {
          c.style.boxShadow = '0 0 0 2px #667eea';
        }
      });
    }
  });

  // Initialize Kan8 when first shown
  const kan8View = document.getElementById('kan8-view');
  let initialized = false;
  
  const observer = new MutationObserver(() => {
    if (kan8View.classList.contains('active') && !initialized) {
      initKan8();
      initialized = true;
    }
  });
  
  observer.observe(kan8View, { attributes: true, attributeFilter: ['class'] });
});