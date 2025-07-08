// Tab functionality
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.nav-link');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Show selected tab content
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked tab
    event.target.classList.add('active');
}

// Modal functionality
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
    event.target.style.display = 'none';
    }
}

// Form handlers
function saveUser(event) {
    event.preventDefault();
    alert('Utilisateur enregistré avec succès!');
    closeModal('userModal');
}

function saveDKit(event) {
    event.preventDefault();
    alert('D-KIT enregistré avec succès!');
    closeModal('dkitModal');
}

function saveAssignment(event) {
    event.preventDefault();
    alert('Assignation créée avec succès!');
    closeModal('assignModal');
}

function updateProfile(event) {
    event.preventDefault();
    alert('Profil mis à jour avec succès!');
}

function reassignKit() {
    if (confirm('Voulez-vous vraiment réassigner ce D-KIT?')) {
    alert('D-KIT réassigné avec succès!');
    }
}

function downloadReport(type) {
    alert('Téléchargement du rapport ' + type + ' en cours...');
}

function logout() {
    if (confirm('Voulez-vous vraiment vous déconnecter?')) {
    alert('Déconnexion en cours...');
    // Redirect to login page
    }
}

// --- D-KITs Logic ---

let dkits = [
  {
    serial: "DKIT-001",
    model: "D-KIT Pro",
    purchaseDate: "27/05/2025",
    status: "En service"
  },
  {
    serial: "DKIT-002",
    model: "D-KIT Standard",
    purchaseDate: "15/05/2025",
    status: "En attente"
  }
];

function getStatusBadgeClass(status) {
  switch(status.toLowerCase()) {
    case 'en service': return 'status-delivered';
    case 'en attente': return 'status-pending';
    case 'en maintenance': return 'status-maintenance';
    case 'défectueux': return 'status-defective';
    default: return 'status-pending';
  }
}

function openDkitDetailsModal(dkitIndex) {
  const dkit = dkits[dkitIndex];
  document.getElementById('detailDkitSerial').textContent = dkit.serial;
  document.getElementById('detailDkitModel').textContent = dkit.model;
  document.getElementById('detailDkitDate').textContent = dkit.purchaseDate;
  document.getElementById('detailDkitStatus').textContent = dkit.status;
  openModal('dkitDetailsModal');
}

function addDKit(event) {
  event.preventDefault();
  const serial = document.getElementById('addDkitSerial').value;
  const model = document.getElementById('addDkitModel').value;
  const purchaseDate = formatDate(document.getElementById('addDkitDate').value);
  const status = document.getElementById('addDkitStatus').value;
  if (dkits.some(dkit => dkit.serial === serial)) {
    alert('Ce numéro de série existe déjà!');
    return;
  }
  dkits.push({ serial, model, purchaseDate, status });
  refreshDkitsTable();
  closeModal('addDkitModal');
  document.querySelector('#addDkitModal form').reset();
  alert('D-KIT ajouté avec succès!');
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR');
}

function refreshDkitsTable() {
  const tbody = document.getElementById('dkitsTableBody');
  if (!tbody) return; // Only run on the D-KITs page
  tbody.innerHTML = '';
  dkits.forEach((dkit, index) => {
    const row = document.createElement('tr');
    row.setAttribute('data-dkit-index', index);
    row.innerHTML = `
      <td>${dkit.serial}</td>
      <td>${dkit.model}</td>
      <td>${dkit.purchaseDate}</td>
      <td><span class="status-badge ${getStatusBadgeClass(dkit.status)}">${dkit.status}</span></td>
      <td>
        <button class="btn btn-secondary btn-small" onclick="openDkitDetailsModal(${index})">
          <i class="fas fa-eye"></i> Détails
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// Load modals and then refresh table (only on D-KITs page)
if (document.getElementById('dkits')) {
  fetch('sales_modals.html')
    .then(response => response.text())
    .then(html => {
      document.getElementById('modalContainer').innerHTML = html;
      refreshDkitsTable();
    })
    .catch(error => {
      console.error('Erreur lors du chargement des modals:', error);
    });
}