const API = "http://localhost:8000";

// STATE
let selectedClientId = null;
let editClientId = null;

// LOAD
document.addEventListener("DOMContentLoaded", () => {
  cargarClientes();

  // DELETE MODAL
  document.getElementById("confirmDelete").onclick = confirmarDelete;
  document.getElementById("cancelDelete").onclick = cerrarDeleteModal;

  // EDIT MODAL
  document.getElementById("confirmEdit").onclick = confirmarEdit;
  document.getElementById("cancelEdit").onclick = cerrarEditModal;
});

// -------------------------
// GET CLIENTS
// -------------------------
async function cargarClientes() {
  const res = await fetch(`${API}/clientes`);
  const data = await res.json();

  const tabla = document.getElementById("tabla");
  tabla.innerHTML = "";

  data.forEach(c => {
    tabla.innerHTML += `
      <tr>
        <td>${c.id}</td>
        <td>${c.nombre}</td>
        <td>${c.apellido}</td>
        <td>${c.edad}</td>
        <td>${c.correo}</td>
        <td>${c.telefono}</td>
        <td>${c.direccion}</td>
        <td>
          <div class="action-buttons">

            <button class="edit-btn" onclick="abrirEditModal(${c.id}, '${c.nombre}', '${c.apellido}', ${c.edad}, '${c.correo}', '${c.telefono}', '${c.direccion}')">
              ✏️
            </button>

            <button class="delete-btn" onclick="abrirDeleteModal(${c.id}, '${c.nombre}')">
              🗑️
            </button>

          </div>
        </td>
      </tr>
    `;
  });
}

// -------------------------
// CREATE
// -------------------------
async function crearCliente() {
  const cliente = {
    nombre: document.getElementById("nombre").value,
    apellido: document.getElementById("apellido").value,
    edad: parseInt(document.getElementById("edad").value),
    correo: document.getElementById("correo").value,
    telefono: document.getElementById("telefono").value,
    direccion: document.getElementById("direccion").value
  };

  await fetch(`${API}/clientes`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(cliente)
  });

  limpiarForm();

  // ⬇️ give Kafka/consumer a moment to persist
  setTimeout(() => {
    cargarClientes();
  }, 500);
}

// -------------------------
// DELETE MODAL
// -------------------------
function abrirDeleteModal(id, nombre) {
  selectedClientId = id;

  document.getElementById("deleteMessage").innerText =
    `¿Estás seguro que quieres eliminar a ${nombre}?`;

  document.getElementById("deleteModal").classList.remove("hidden");
}

async function confirmarDelete() {
  await fetch(`${API}/clientes/${selectedClientId}`, {
    method: "DELETE"
  });

  cerrarDeleteModal();
  
  // ⬇️ give Kafka/consumer a moment to persist
  setTimeout(() => {
    cargarClientes();
  }, 500);
}

function cerrarDeleteModal() {
  document.getElementById("deleteModal").classList.add("hidden");
  selectedClientId = null;
}

// -------------------------
// EDIT MODAL
// -------------------------
function abrirEditModal(id, nombre, apellido, edad, correo, telefono, direccion) {
  editClientId = id;

  document.getElementById("edit_nombre").value = nombre;
  document.getElementById("edit_apellido").value = apellido;
  document.getElementById("edit_edad").value = edad;
  document.getElementById("edit_correo").value = correo;
  document.getElementById("edit_telefono").value = telefono;
  document.getElementById("edit_direccion").value = direccion;

  document.getElementById("editModal").classList.remove("hidden");
}

async function confirmarEdit() {
  const updated = {
    nombre: document.getElementById("edit_nombre").value,
    apellido: document.getElementById("edit_apellido").value,
    edad: parseInt(document.getElementById("edit_edad").value),
    correo: document.getElementById("edit_correo").value,
    telefono: document.getElementById("edit_telefono").value,
    direccion: document.getElementById("edit_direccion").value
  };

  await fetch(`${API}/clientes/${editClientId}`, {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(updated)
  });

  cerrarEditModal();
  
  // ⬇️ give Kafka/consumer a moment to persist
  setTimeout(() => {
    cargarClientes();
  }, 500);
}

function cerrarEditModal() {
  document.getElementById("editModal").classList.add("hidden");
  editClientId = null;
}

// -------------------------
// UTILS
// -------------------------
function limpiarForm() {
  document.getElementById("nombre").value = "";
  document.getElementById("apellido").value = "";
  document.getElementById("edad").value = "";
  document.getElementById("correo").value = "";
  document.getElementById("telefono").value = "";
  document.getElementById("direccion").value = "";
}

// -------------------------
// LOGS
// -------------------------
document.addEventListener("DOMContentLoaded", () => {

  const box = document.getElementById("kafkaLogs");

  const empty = document.createElement("div");
  empty.id = "noLogs";
  empty.classList.add("log-line");
  empty.style.opacity = "0.6";
  empty.style.fontStyle = "italic";
  empty.textContent = "No hay logs para mostrar";

  box.appendChild(empty);

  const logSocket = new WebSocket("ws://localhost:8000/ws/logs");

  logSocket.onopen = () => {
    console.log("🟢 WebSocket connected");
  };

  logSocket.onclose = () => {
    console.log("🔴 WebSocket disconnected");
  };

  logSocket.onerror = (e) => {
    console.log("⚠️ WebSocket error:", e);
  };

  logSocket.onmessage = (event) => {
    addKafkaLog(event.data);
  };

});

function addKafkaLog(message) {
  const box = document.getElementById("kafkaLogs");

  if (!box) {
    console.warn("Kafka log container not found");
    return;
  }

  // remove "no logs" placeholder if it exists
  const empty = document.getElementById("noLogs");
  if (empty) {
    empty.remove();
  }

  const line = document.createElement("div");
  line.classList.add("log-line");
  line.textContent = message;

  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}