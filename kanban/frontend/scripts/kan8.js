// scripts/kan8.js - COMPLETE REBUILD
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Kan8 initializing...');
  
  const kan8Cards = document.getElementById('kan8Cards');
  const addCardBtn = document.getElementById('kan8-add-card');
  const svg = document.getElementById('kan8Connections');
  const canvas = document.getElementById('kan8Canvas');
  
  if (!kan8Cards || !addCardBtn || !svg || !canvas) {
    console.error('❌ Kan8 elements not found!');
    return;
  }
  
  console.log('✅ All Kan8 elements found');
  
  // State
  let cardIdCounter = 1;
  let connections = [];
  let isConnecting = false;
  let connectionStart = null;
  let tempLine = null;
  
  // ===================================
  // CREATE CARD
  // ===================================
  function createCard(title, tech, desc, icon, x, y) {
    const card = document.createElement('div');
    const cardId = `card-${cardIdCounter++}`;
    
    card.className = 'kan8-card';
    card.dataset.cardId = cardId;
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
        <i class="fas fa-trash" title="Delete"></i>
      </div>
      <div class="kan8-connection-point top" data-side="top"></div>
      <div class="kan8-connection-point right" data-side="right"></div>
      <div class="kan8-connection-point bottom" data-side="bottom"></div>
      <div class="kan8-connection-point left" data-side="left"></div>
    `;
    
    // Make draggable
    setupCardDrag(card);
    
    // Setup connection points
    setupConnectionPoints(card);
    
    // Delete button
    card.querySelector('.fa-trash').addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Delete this card?')) {
        deleteCard(cardId);
      }
    });
    
    return card;
  }
  
  // ===================================
  // CARD DRAGGING - OPTIMIZED
  // ===================================
  function setupCardDrag(card) {
    let isDragging = false;
    let startX, startY, initialLeft, initialTop;
    let animationFrameId = null;
    
    card.addEventListener('mousedown', (e) => {
      // Don't drag if clicking on actions or connection points
      if (e.target.closest('.kan8-card-actions')) return;
      if (e.target.classList.contains('kan8-connection-point')) return;
      
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      initialLeft = parseInt(card.style.left);
      initialTop = parseInt(card.style.top);
      
      card.style.cursor = 'grabbing';
      card.style.zIndex = '1000';
      
      e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      
      // Update card position immediately
      card.style.left = `${initialLeft + dx}px`;
      card.style.top = `${initialTop + dy}px`;
      
      // Throttle connection redrawing using requestAnimationFrame
      if (animationFrameId === null) {
        animationFrameId = requestAnimationFrame(() => {
          redrawAllConnections();
          animationFrameId = null;
        });
      }
    });
    
    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        card.style.cursor = 'grab';
        card.style.zIndex = '';
        
        // Final redraw to ensure accuracy
        if (animationFrameId !== null) {
          cancelAnimationFrame(animationFrameId);
          animationFrameId = null;
        }
        redrawAllConnections();
      }
    });
  }
  
  
  // ===================================
  // CONNECTION POINTS
  // ===================================
  function setupConnectionPoints(card) {
    const points = card.querySelectorAll('.kan8-connection-point');
    
    points.forEach(point => {
      point.addEventListener('click', (e) => {
        e.stopPropagation();
        handleConnectionPointClick(card, point);
      });
    });
  }
  
  function handleConnectionPointClick(card, point) {
    const cardId = card.dataset.cardId;
    const side = point.dataset.side;
    
    if (!isConnecting) {
      // Start new connection
      console.log('🔗 Starting connection from:', cardId, side);
      startNewConnection(card, point, cardId, side);
    } else {
      // Complete connection
      if (connectionStart.cardId === cardId) {
        console.log('❌ Cannot connect card to itself');
        cancelConnection();
        return;
      }
      
      console.log('✅ Completing connection to:', cardId, side);
      completeConnection(cardId, side);
    }
  }
  
  function startNewConnection(card, point, cardId, side) {
    isConnecting = true;
    connectionStart = { card, point, cardId, side };
    
    // Visual feedback
    point.classList.add('active');
    card.classList.add('connecting-from');
    canvas.classList.add('connecting-mode');
    
    // Create temp line
    tempLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    tempLine.classList.add('temp-connection-line');
    tempLine.setAttribute('stroke', '#4299e1');
    tempLine.setAttribute('stroke-width', '2.5');
    tempLine.setAttribute('stroke-dasharray', '8,5');
    tempLine.setAttribute('fill', 'none');
    svg.appendChild(tempLine);
    
    console.log('✅ Temp line created');
  }
  
  function completeConnection(toCardId, toSide) {
    const connection = {
      id: `conn-${Date.now()}`,
      from: {
        cardId: connectionStart.cardId,
        side: connectionStart.side
      },
      to: {
        cardId: toCardId,
        side: toSide
      }
    };
    
    connections.push(connection);
    console.log('✅ Connection created:', connection);
    
    drawConnection(connection);
    cancelConnection();
  }
  
  function cancelConnection() {
    if (connectionStart) {
      connectionStart.point.classList.remove('active');
      connectionStart.card.classList.remove('connecting-from');
    }
    
    canvas.classList.remove('connecting-mode');
    
    if (tempLine && tempLine.parentNode) {
      tempLine.remove();
    }
    
    isConnecting = false;
    connectionStart = null;
    tempLine = null;
    
    console.log('🔄 Connection cancelled');
  }
  
  // Update temp line on mouse move
  document.addEventListener('mousemove', (e) => {
    if (!isConnecting || !tempLine || !connectionStart) return;
    
    const rect = canvas.getBoundingClientRect();
    const startPos = getConnectionPointPosition(connectionStart.card, connectionStart.point);
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;
    
    const path = createPath(startPos.x, startPos.y, endX, endY);
    tempLine.setAttribute('d', path);
  });
  
  // Cancel on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isConnecting) {
      cancelConnection();
    }
  });
  
  // ===================================
  // DRAW CONNECTIONS
  // ===================================
  function drawConnection(connection) {
    const fromCard = document.querySelector(`[data-card-id="${connection.from.cardId}"]`);
    const toCard = document.querySelector(`[data-card-id="${connection.to.cardId}"]`);
    
    if (!fromCard || !toCard) {
      console.error('❌ Cards not found for connection:', connection);
      return;
    }
    
    const fromPoint = fromCard.querySelector(`[data-side="${connection.from.side}"]`);
    const toPoint = toCard.querySelector(`[data-side="${connection.to.side}"]`);
    
    if (!fromPoint || !toPoint) {
      console.error('❌ Connection points not found');
      return;
    }
    
    const startPos = getConnectionPointPosition(fromCard, fromPoint);
    const endPos = getConnectionPointPosition(toCard, toPoint);
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const pathString = createPath(startPos.x, startPos.y, endPos.x, endPos.y);
    
    path.setAttribute('d', pathString);
    path.setAttribute('stroke', '#4299e1');
    path.setAttribute('stroke-width', '2.5');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-linecap', 'round');
    path.classList.add('connection-line');
    path.dataset.connectionId = connection.id;
    
    // Hover effect
    path.addEventListener('mouseenter', () => {
      path.setAttribute('stroke', '#f56565');
      path.setAttribute('stroke-width', '3.5');
    });
    
    path.addEventListener('mouseleave', () => {
      path.setAttribute('stroke', '#4299e1');
      path.setAttribute('stroke-width', '2.5');
    });
    
    // Delete on click
    path.addEventListener('click', () => {
      if (confirm('Delete this connection?')) {
        deleteConnection(connection.id);
      }
    });
    
    svg.appendChild(path);
    
    // Mark cards as connected
    fromCard.classList.add('has-connections');
    toCard.classList.add('has-connections');
    
    console.log('✅ Connection drawn:', connection.id);
  }
  
  function getConnectionPointPosition(card, point) {
    const canvasRect = canvas.getBoundingClientRect();
    const pointRect = point.getBoundingClientRect();
    
    return {
      x: pointRect.left + pointRect.width / 2 - canvasRect.left,
      y: pointRect.top + pointRect.height / 2 - canvasRect.top
    };
  }
  
  function createPath(x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const absDx = Math.abs(dx);
    
    // Use a gentler curve - only 25% of horizontal distance
    const offset = Math.min(absDx * 0.25, 100);
    
    const cx1 = x1 + offset;
    const cy1 = y1;
    const cx2 = x2 - offset;
    const cy2 = y2;
    
    return `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
  }
  
  function redrawAllConnections() {
    // Remove all existing connection lines
    const existingLines = svg.querySelectorAll('.connection-line');
    existingLines.forEach(line => line.remove());
    
    // Redraw all connections
    connections.forEach(conn => drawConnection(conn));
  }
  
  // ===================================
  // DELETE
  // ===================================
  function deleteConnection(connectionId) {
    connections = connections.filter(c => c.id !== connectionId);
    
    const path = svg.querySelector(`[data-connection-id="${connectionId}"]`);
    if (path) path.remove();
    
    console.log('🗑️ Connection deleted:', connectionId);
  }
  
  function deleteCard(cardId) {
    // Remove connections
    connections = connections.filter(conn => {
      if (conn.from.cardId === cardId || conn.to.cardId === cardId) {
        const path = svg.querySelector(`[data-connection-id="${conn.id}"]`);
        if (path) path.remove();
        return false;
      }
      return true;
    });
    
    // Remove card
    const card = document.querySelector(`[data-card-id="${cardId}"]`);
    if (card) card.remove();
    
    console.log('🗑️ Card deleted:', cardId);
  }
  
  // ===================================
  // ADD CARD BUTTON
  // ===================================
  addCardBtn.addEventListener('click', () => {
    const x = 100 + Math.random() * 400;
    const y = 100 + Math.random() * 300;
    const card = createCard('New Component', 'JavaScript', 'Click to edit', '📄', x, y);
    kan8Cards.appendChild(card);
    console.log('➕ Card added');
  });
  
  // ===================================
  // INITIALIZE
  // ===================================
  function initKan8() {
    console.log('🎬 Initializing Kan8 with sample cards...');
    
    if (kan8Cards.children.length > 0) {
      console.log('⚠️ Cards already exist, skipping init');
      return;
    }
    
    const card1 = createCard('Login.jsx', 'React Component', 'User authentication form', '⚛️', 100, 150);
    const card2 = createCard('AuthAPI', 'Node.js / Express', 'Authentication endpoint', '🟢', 500, 150);
    const card3 = createCard('User DB', 'PostgreSQL', 'User credentials table', '🗄️', 900, 150);
    
    kan8Cards.appendChild(card1);
    kan8Cards.appendChild(card2);
    kan8Cards.appendChild(card3);
    
    // Auto-create sample connections
    setTimeout(() => {
      console.log('🔗 Creating sample connections...');
      
      connections.push({
        id: 'conn-sample-1',
        from: { cardId: 'card-1', side: 'right' },
        to: { cardId: 'card-2', side: 'left' }
      });
      
      connections.push({
        id: 'conn-sample-2',
        from: { cardId: 'card-2', side: 'right' },
        to: { cardId: 'card-3', side: 'left' }
      });
      
      redrawAllConnections();
      console.log('✅ Sample connections created');
    }, 200);
  }
  
  // ===================================
  // OBSERVER FOR VIEW ACTIVATION
  // ===================================
  const kan8View = document.getElementById('kan8-view');
  if (!kan8View) {
    console.error('❌ Kan8 view not found!');
    return;
  }
  
  let initialized = false;
  
  const observer = new MutationObserver(() => {
    if (kan8View.classList.contains('active') && !initialized) {
      console.log('👁️ Kan8 view activated');
      initKan8();
      initialized = true;
    }
  });
  
  observer.observe(kan8View, {
    attributes: true,
    attributeFilter: ['class']
  });
  
  console.log('✅ Kan8 initialization complete');
});



// scripts/kan8.js
// document.addEventListener('DOMContentLoaded', () => {
//   const kan8Cards = document.getElementById('kan8Cards');
//   const kan8Connections = document.getElementById('kan8Connections');
//   const addCardBtn = document.getElementById('kan8-add-card');
  
//   if (!kan8Cards || !kan8Connections) return;

//   let cardId = 1;
//   let connections = [];
//   let isConnecting = false;
//   let startCard = null;
//   let startPoint = null;

//   // Create connection line with unique ID
//   function createConnectionLine(x1, y1, x2, y2, id) {
//     const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
//     line.setAttribute('x1', x1);
//     line.setAttribute('y1', y1);
//     line.setAttribute('x2', x2);
//     line.setAttribute('y2', y2);
//     line.setAttribute('stroke', '#667eea');
//     line.setAttribute('stroke-width', '2');
//     line.setAttribute('marker-end', 'url(#arrowhead)');
//     line.setAttribute('class', 'kan8-connection-line');
//     line.dataset.connectionId = id;
//     return line;
//   }

//   // Get connection point position
//   function getConnectionPoint(card, side) {
//     const rect = card.getBoundingClientRect();
//     const containerRect = kan8Cards.getBoundingClientRect();
    
//     switch(side) {
//       case 'top': return { x: rect.left + rect.width/2 - containerRect.left, y: rect.top - containerRect.top };
//       case 'right': return { x: rect.right - containerRect.left, y: rect.top + rect.height/2 - containerRect.top };
//       case 'bottom': return { x: rect.left + rect.width/2 - containerRect.left, y: rect.bottom - containerRect.top };
//       case 'left': return { x: rect.left - containerRect.left, y: rect.top + rect.height/2 - containerRect.top };
//       default: return { x: rect.left + rect.width/2 - containerRect.left, y: rect.top + rect.height/2 - containerRect.top };
//     }
//   }

//   // Update all connections with proper anchor points
//   function updateConnections() {
//     while (kan8Connections.firstChild) {
//       kan8Connections.removeChild(kan8Connections.firstChild);
//     }
    
//     connections.forEach((conn, index) => {
//       const fromCard = document.querySelector(`[data-card-id="${conn.from.card}"]`);
//       const toCard = document.querySelector(`[data-card-id="${conn.to.card}"]`);
      
//       if (fromCard && toCard) {
//         const fromPoint = getConnectionPoint(fromCard, conn.from.side);
//         const toPoint = getConnectionPoint(toCard, conn.to.side);
        
//         const line = createConnectionLine(fromPoint.x, fromPoint.y, toPoint.x, toPoint.y, `conn-${index}`);
//         kan8Connections.appendChild(line);
        
//         // Add click handler to delete connection
//         line.addEventListener('click', (e) => {
//           e.stopPropagation();
//           connections.splice(index, 1);
//           updateConnections();
//           updateCardGlow();
//         });
//       }
//     });
    
//     updateCardGlow();
//   }

//   // Add glow to connected cards
//   function updateCardGlow() {
//     document.querySelectorAll('.kan8-card').forEach(card => {
//       card.classList.remove('connected');
//     });
    
//     connections.forEach(conn => {
//       const fromCard = document.querySelector(`[data-card-id="${conn.from.card}"]`);
//       const toCard = document.querySelector(`[data-card-id="${conn.to.card}"]`);
//       if (fromCard) fromCard.classList.add('connected');
//       if (toCard) toCard.classList.add('connected');
//     });
//   }

//   // Create card
//   function createCard(title, tech, desc, icon, x = 100, y = 100) {
//     const card = document.createElement('div');
//     card.className = 'kan8-card';
//     card.dataset.cardId = `card-${cardId++}`;
//     card.style.left = `${x}px`;
//     card.style.top = `${y}px`;
    
//     card.innerHTML = `
//       <div class="kan8-card-header">
//         <span class="kan8-card-icon">${icon}</span>
//         <span class="kan8-card-title">${title}</span>
//       </div>
//       <div class="kan8-card-body">
//         <span class="kan8-card-tech">${tech}</span>
//         <p class="kan8-card-desc">${desc}</p>
//       </div>
//       <div class="kan8-card-actions">
//         <i class="fas fa-pen" title="Edit"></i>
//         <i class="fas fa-link" title="Connect"></i>
//         <i class="fas fa-trash" title="Delete"></i>
//       </div>
//       <div class="kan8-connection-point top" data-side="top"></div>
//       <div class="kan8-connection-point right" data-side="right"></div>
//       <div class="kan8-connection-point bottom" data-side="bottom"></div>
//       <div class="kan8-connection-point left" data-side="left"></div>
//     `;
    
//     // Card dragging
//     card.addEventListener('mousedown', (e) => {
//       if (e.target.closest('.kan8-card-actions')) return;
//       if (e.target.classList.contains('kan8-connection-point')) return;
      
//       const startX = e.clientX - card.offsetLeft;
//       const startY = e.clientY - card.offsetTop;
      
//       const move = (e) => {
//         card.style.left = `${e.clientX - startX}px`;
//         card.style.top = `${e.clientY - startY}px`;
//         updateConnections();
//       };
      
//       const stop = () => {
//         document.removeEventListener('mousemove', move);
//         document.removeEventListener('mouseup', stop);
//       };
      
//       document.addEventListener('mousemove', move);
//       document.addEventListener('mouseup', stop);
//     });
    
//     // Handle connection start from connection points
//     card.querySelectorAll('.kan8-connection-point').forEach(point => {
//       point.addEventListener('mousedown', (e) => {
//         e.stopPropagation();
//         isConnecting = true;
//         startCard = { card: card.dataset.cardId, side: point.dataset.side };
        
//         // Highlight all connection points on other cards
//         document.querySelectorAll('.kan8-connection-point').forEach(p => {
//           const pCard = p.closest('.kan8-card');
//           if (pCard.dataset.cardId !== card.dataset.cardId) {
//             p.style.background = '#ff6b6b';
//           }
//         });
//       });
//     });
    
//     return card;
//   }

//   // Initialize
//   function initKan8() {
//     if (kan8Cards.children.length > 0) return;
    
//     kan8Cards.appendChild(createCard('Login.jsx', 'React Component', 'User authentication form', '⚛️', 100, 100));
//     kan8Cards.appendChild(createCard('AuthAPI', 'Node.js / Express', 'Authentication endpoint', '🟢', 450, 100));
//     kan8Cards.appendChild(createCard('User DB', 'PostgreSQL', 'User credentials table', '🗄️', 800, 100));
    
//     // Sample connections (from right of card 1 to left of card 2)
//     connections.push({ 
//       from: { card: 'card-1', side: 'right' }, 
//       to: { card: 'card-2', side: 'left' } 
//     });
//     connections.push({ 
//       from: { card: 'card-2', side: 'right' }, 
//       to: { card: 'card-3', side: 'left' } 
//     });
    
//     updateConnections();
//   }

//   // Add card
//   if (addCardBtn) {
//     addCardBtn.addEventListener('click', () => {
//       const x = 100 + Math.random() * 200;
//       const y = 200 + Math.random() * 200;
//       kan8Cards.appendChild(createCard('New File.js', 'JavaScript', 'Click to edit', '📄', x, y));
//     });
//   }

//   // Handle connection completion
//   document.addEventListener('mouseup', () => {
//     if (!isConnecting) return;
    
//     // Reset connection points
//     document.querySelectorAll('.kan8-connection-point').forEach(p => {
//       p.style.background = '#667eea';
//     });
    
//     isConnecting = false;
//     startCard = null;
//   });

//   // Handle connection point drop
//   document.addEventListener('click', (e) => {
//     if (!isConnecting) return;
    
//     const targetPoint = e.target.closest('.kan8-connection-point');
//     if (targetPoint && startCard) {
//       const targetCard = targetPoint.closest('.kan8-card');
//       const targetSide = targetPoint.dataset.side;
      
//       if (targetCard.dataset.cardId !== startCard.card) {
//         connections.push({
//           from: startCard,
//           to: { card: targetCard.dataset.cardId, side: targetSide }
//         });
//         updateConnections();
//       }
      
//       // Reset
//       document.querySelectorAll('.kan8-connection-point').forEach(p => {
//         p.style.background = '#667eea';
//       });
//       isConnecting = false;
//       startCard = null;
//     }
//   });

//   // Initialize when view is active
//   const kan8View = document.getElementById('kan8-view');
//   let initialized = false;
  
//   const observer = new MutationObserver(() => {
//     if (kan8View.classList.contains('active') && !initialized) {
//       initKan8();
//       initialized = true;
//     }
//   });
  
//   observer.observe(kan8View, { attributes: true, attributeFilter: ['class'] });
// });