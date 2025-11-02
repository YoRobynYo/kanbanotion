document.addEventListener('DOMContentLoaded', () => {

  // Auto-convert old tasks (no .task-text)
  document.querySelectorAll('.task:not(:has(.task-text))').forEach(task => {
    const text = task.innerText.trim();
    task.innerHTML = `
      <span class="task-text">${text}</span>
      <div class="task-actions">
        <i class="fas fa-pen"></i>
        <i class="fas fa-trash"></i>
      </div>`;
  });

  function saveData() {
    const columns = [];
    document.querySelectorAll('.kanban-column').forEach(column => {
      const columnId = column.id;
      const tasks = [];
      column.querySelectorAll('.task .task-text').forEach(taskTextElement => {
        tasks.push(taskTextElement.innerText);
      });
      columns.push({ columnId, tasks });
    });
    localStorage.setItem('kanban-data', JSON.stringify(columns));
  }

  function loadData() {
    const savedData = localStorage.getItem('kanban-data');
    if (!savedData) {
      initializeDragAndDrop();
      return;
    }

    const columns = JSON.parse(savedData);
    document.querySelectorAll('.tasks').forEach(container => container.innerHTML = '');

    columns.forEach(columnData => {
      const columnElement = document.getElementById(columnData.columnId);
      if (columnElement) {
        const tasksContainer = columnElement.querySelector('.tasks');
        columnData.tasks.forEach(taskText => {
          const newTask = createTaskElement(taskText);
          tasksContainer.appendChild(newTask);
        });
      }
    });
    initializeDragAndDrop();
  }

  function createTaskElement(text) {
    const task = document.createElement('div');
    task.classList.add('task');
    task.setAttribute('draggable', 'true');

    const taskText = document.createElement('span');
    taskText.classList.add('task-text');
    taskText.innerText = text;

    const taskActions = document.createElement('div');
    taskActions.classList.add('task-actions');

    const editIcon = document.createElement('i');
    editIcon.classList.add('fas', 'fa-pen');
    editIcon.addEventListener('click', () => handleEdit(task, taskText));

    const deleteIcon = document.createElement('i');
    deleteIcon.classList.add('fas', 'fa-trash');
    deleteIcon.addEventListener('click', () => handleDelete(task, taskText));

    taskActions.appendChild(editIcon);
    taskActions.appendChild(deleteIcon);
    task.appendChild(taskText);
    task.appendChild(taskActions);
    return task;
  }

  function handleEdit(task, taskText) {
    task.setAttribute('draggable', 'false');
    const input = document.createElement('input');
    input.type = 'text';
    input.value = taskText.innerText;
    input.classList.add('task-editing-input');
    task.replaceChild(input, taskText);
    input.focus();

    const finishEdit = () => {
      taskText.innerText = input.value.trim() || "Untitled Task";
      task.replaceChild(taskText, input);
      task.setAttribute('draggable', 'true');
      saveData();
    };
    input.addEventListener('blur', finishEdit);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') finishEdit(); });
  }

  function handleDelete(task, taskText) {
    if (confirm(`Delete this task?\n"${taskText.innerText}"`)) {
      task.remove();
      saveData();
    }
  }

  // ✅ UPDATED: initializeDragAndDrop with ghost removal only
  function initializeDragAndDrop() {
    const tasks = document.querySelectorAll('.task');
    const taskContainers = document.querySelectorAll('.tasks');

    tasks.forEach(task => {
      const dragStartHandler = (e) => {
        task.classList.add('dragging');

        // 👻 Hide the default drag ghost
        const ghost = document.createElement('div');
        ghost.style.width = '0';
        ghost.style.height = '0';
        ghost.style.opacity = '0';
        ghost.style.position = 'absolute';
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 0, 0);

        const dragEndHandler = () => {
          task.classList.remove('dragging');
  
          // 👇 ADD THESE TWO LINES for smooth drop
          task.classList.add('smooth-drop');
          setTimeout(() => task.classList.remove('smooth-drop'), 300);
  
          if (ghost.parentNode) ghost.remove(); // clean up
          saveData();
        };

        task.addEventListener('dragend', dragEndHandler);
      };

      // Remove any existing listener to avoid duplicates
      task.removeEventListener('dragstart', dragStartHandler);
      task.addEventListener('dragstart', dragStartHandler);
    });

    taskContainers.forEach(container => {
      container.addEventListener('dragover', e => {
        e.preventDefault();
        const draggingTask = document.querySelector('.dragging');
        if (!draggingTask) return;

        const afterElement = getDragAfterElement(container, e.clientY);
        if (afterElement) {
          container.insertBefore(draggingTask, afterElement);
        } else {
          container.appendChild(draggingTask);
        }
      });
    });
  }

  function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.task:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      return (offset < 0 && offset > closest.offset)
        ? { offset, element: child }
        : closest;
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }

  document.querySelectorAll('.add-task-form').forEach(form => {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const input = form.querySelector('input');
      const taskText = input.value.trim();
      if (taskText) {
        const newTask = createTaskElement(taskText);
        const tasksContainer = form.previousElementSibling;
        tasksContainer.appendChild(newTask);
        input.value = '';
        initializeDragAndDrop(); // Rebind for new task
        saveData();
      }
    });
  });

  loadData();
});



// js/main.js

// document.addEventListener('DOMContentLoaded', () => {

//     function saveData() {
//         const columns = [];
//         document.querySelectorAll('.kanban-column').forEach(column => {
//             const columnId = column.id;
//             const tasks = [];
//             // CRITICAL CHANGE: We now select the '.task-text' span inside each task
//             // to avoid saving the icon text ("pencil-alt", "trash-alt").
//             column.querySelectorAll('.task .task-text').forEach(taskTextElement => {
//                 tasks.push(taskTextElement.innerText);
//             });
//             columns.push({ columnId, tasks });
//         });
//         localStorage.setItem('kanban-data', JSON.stringify(columns));
//     }

//     function loadData() {
//         const savedData = localStorage.getItem('kanban-data');
//         if (!savedData) {
//             // If no saved data, just make the default HTML tasks functional.
//             document.querySelectorAll('.task').forEach(task => {
//                 const text = task.innerText;
//                 const newTask = createTaskElement(text);
//                 task.replaceWith(newTask);
//             });
//             initializeDragAndDrop();
//             return;
//         }

//         const columns = JSON.parse(savedData);
//         document.querySelectorAll('.tasks').forEach(container => container.innerHTML = '');

//         columns.forEach(columnData => {
//             const columnElement = document.getElementById(columnData.columnId);
//             if (columnElement) {
//                 const tasksContainer = columnElement.querySelector('.tasks');
//                 columnData.tasks.forEach(taskText => {
//                     const newTask = createTaskElement(taskText);
//                     tasksContainer.appendChild(newTask);
//                 });
//             }
//         });
//         initializeDragAndDrop();
//     }
    
//     // --- UPGRADED: createTaskElement now builds the entire task with text and icons ---
//     function createTaskElement(text) {
//         const task = document.createElement('div');
//         task.classList.add('task');
//         task.setAttribute('draggable', 'true');

//         const taskText = document.createElement('span');
//         taskText.classList.add('task-text');
//         taskText.innerText = text;

//         const taskActions = document.createElement('div');
//         taskActions.classList.add('task-actions');

//         const editIcon = document.createElement('i');
//         editIcon.classList.add('fas', 'fa-pencil-alt');
//         editIcon.addEventListener('click', () => handleEdit(task, taskText));

//         const deleteIcon = document.createElement('i');
//         deleteIcon.classList.add('fas', 'fa-trash-alt');
//         deleteIcon.addEventListener('click', () => handleDelete(task, taskText));

//         taskActions.appendChild(editIcon);
//         taskActions.appendChild(deleteIcon);
//         task.appendChild(taskText);
//         task.appendChild(taskActions);
        
//         return task;
//     }

//     // --- NEW: Helper function to handle the edit logic ---
//     function handleEdit(task, taskText) {
//         task.setAttribute('draggable', 'false');
//         const input = document.createElement('input');
//         input.type = 'text';
//         input.value = taskText.innerText;
//         input.classList.add('task-editing-input');
        
//         task.replaceChild(input, taskText);
//         input.focus();

//         const finishEdit = () => {
//             taskText.innerText = input.value.trim() ? input.value.trim() : "Untitled Task";
//             task.replaceChild(taskText, input);
//             task.setAttribute('draggable', 'true');
//             saveData();
//         };
        
//         input.addEventListener('blur', finishEdit);
//         input.addEventListener('keydown', e => { if (e.key === 'Enter') finishEdit(); });
//     }

//     // --- NEW: Helper function to handle the delete logic ---
//     function handleDelete(task, taskText) {
//         if (confirm(`Are you sure you want to delete this task?\n\n"${taskText.innerText}"`)) {
//             task.remove();
//             saveData();
//         }
//     }

//     // --- The rest of the file is mostly the same ---

//     function initializeDragAndDrop() {
//         const tasks = document.querySelectorAll('.task');
//         const taskContainers = document.querySelectorAll('.tasks');

//         tasks.forEach(task => {
//             task.addEventListener('dragstart', () => task.classList.add('dragging'));
//             task.addEventListener('dragend', () => {
//                 task.classList.remove('dragging');
//                 saveData();
//             });
//         });

//         taskContainers.forEach(container => {
//             container.addEventListener('dragover', e => {
//                 e.preventDefault();
//                 const draggingTask = document.querySelector('.dragging');
//                 const afterElement = getDragAfterElement(container, e.clientY);
//                 if (afterElement == null) {
//                     container.appendChild(draggingTask);
//                 } else {
//                     container.insertBefore(draggingTask, afterElement);
//                 }
//             });
//         });
//     }

//     function getDragAfterElement(container, y) {
//         const draggableElements = [...container.querySelectorAll('.task:not(.dragging)')];
//         return draggableElements.reduce((closest, child) => {
//             const box = child.getBoundingClientRect();
//             const offset = y - box.top - box.height / 2;
//             if (offset < 0 && offset > closest.offset) {
//                 return { offset: offset, element: child };
//             } else {
//                 return closest;
//             }
//         }, { offset: Number.NEGATIVE_INFINITY }).element;
//     }

//     const addTaskForms = document.querySelectorAll('.add-task-form');
//     addTaskForms.forEach(form => {
//         form.addEventListener('submit', e => {
//             e.preventDefault();
//             const input = form.querySelector('input');
//             const taskText = input.value.trim();
//             if (taskText) {
//                 const newTask = createTaskElement(taskText);
//                 const tasksContainer = form.previousElementSibling;
//                 tasksContainer.appendChild(newTask);
//                 input.value = '';
//                 initializeDragAndDrop();
//                 saveData();
//             }
//         });
//     });

//     loadData();
// });