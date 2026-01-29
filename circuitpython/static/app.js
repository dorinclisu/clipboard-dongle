const replacements = {};

function switchTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });

  // Show selected tab
  document.getElementById(tabName + '-tab').classList.add('active');
  event.target.classList.add('active');

  // Load replacements when switching to replacements tab
  if (tabName === 'replacements') {
    loadReplacements();
  }
}

function loadReplacements() {
  fetch('/replacements')
    .then(response => response.json())
    .then(data => {
      Object.assign(replacements, data);
      renderReplacementsTable(data);
    })
    .catch(error => {
      showMessage('replacements-message', 'Error loading replacements: ' + error.message, 'error');
    });
}

function renderReplacementsTable(data) {
  const tbody = document.getElementById('replacementsBody');
  tbody.innerHTML = '';

  for (const [char, replacement] of Object.entries(data)) {
    addReplacementRowWithData(char, replacement);
  }

  // Add one empty row for convenience
  if (Object.keys(data).length === 0) {
    addReplacementRow();
  }
}

function addReplacementRowWithData(char, replacement) {
  const tbody = document.getElementById('replacementsBody');
  const row = tbody.insertRow();

  const cellChar = row.insertCell(0);
  const cellReplacement = row.insertCell(1);
  const cellAction = row.insertCell(2);

  const inputChar = document.createElement('input');
  inputChar.type = 'text';
  inputChar.value = char;
  inputChar.maxLength = 1;
  inputChar.placeholder = 'Character';
  cellChar.appendChild(inputChar);

  const inputReplacement = document.createElement('input');
  inputReplacement.type = 'text';
  inputReplacement.value = replacement;
  inputReplacement.placeholder = 'ASCII replacement';
  cellReplacement.appendChild(inputReplacement);

  cellAction.innerHTML = `<button type="button" class="delete-btn" onclick="deleteReplacementRow(this)">Delete</button>`;
}

function addReplacementRow() {
  addReplacementRowWithData('', '');
}

function deleteReplacementRow(button) {
  const row = button.parentNode.parentNode;
  row.parentNode.removeChild(row);
}

function saveReplacements() {
  const tbody = document.getElementById('replacementsBody');
  const rows = tbody.getElementsByTagName('tr');
  const newReplacements = {};

  for (let i = 0; i < rows.length; i++) {
    const inputs = rows[i].getElementsByTagName('input');
    const char = inputs[0].value;
    const replacement = inputs[1].value;

    if (char && replacement) {
      newReplacements[char] = replacement;
    }
  }

  fetch('/replacements', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(newReplacements)
  })
  .then(response => {
    if (response.ok) {
      // Clear all existing replacements
      Object.keys(replacements).forEach(key => delete replacements[key]);
      // Assign new replacements
      Object.assign(replacements, newReplacements);
      showMessage('replacements-message', 'Replacements saved successfully!', 'success');
    } else {
      return response.text().then(errorText => {
        throw new Error(errorText || 'Failed to save');
      });
    }
  })
  .catch(error => {
    showMessage('replacements-message', 'Error: ' + error.message, 'error');
  });
}

function showMessage(elementId, text, type) {
  const messageDiv = document.getElementById(elementId);
  messageDiv.textContent = text;
  messageDiv.className = 'message ' + type;
  messageDiv.style.display = 'block';
  setTimeout(() => {
    messageDiv.style.display = 'none';
  }, 3000);
}

function normalizeToAscii(text) {
  // Normalize Unicode to NFD (decompose accents from base characters) then remove combining diacritical marks
  let normalized = text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  // Apply explicit replacements for characters that don't decompose
  return normalized.replace(/[^\x00-\x7F]/g, char => replacements[char] || char);
}

function clearText() {
  document.getElementById('textInput').value = '';
  document.getElementById('textInput').focus();
}

// Handle paste events to prevent URL encoding
document.getElementById('textInput').addEventListener('paste', function(e) {
  e.preventDefault();
  const pastedText = (e.clipboardData || window.clipboardData).getData('text/plain');
  const normalizedText = normalizeToAscii(pastedText);
  const textarea = e.target;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const text = textarea.value;
  // Insert the normalized text at cursor position
  textarea.value = text.substring(0, start) + normalizedText + text.substring(end);
  // Set cursor position after pasted text
  textarea.selectionStart = textarea.selectionEnd = start + normalizedText.length;
});

document.getElementById('textForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const text = document.getElementById('textInput').value;

  fetch('/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'text/plain'
    },
    body: text
  })
  .then(response => {
    if (response.ok) {
      showMessage('message', 'Text sent successfully!', 'success');
    } else {
      return response.text().then(errorText => {
        throw new Error(errorText || 'Failed to send');
      });
    }
  })
  .catch(error => {
    showMessage('message', error.message, 'error');
  });
});
