const API_URL = `${window.location.origin}/api`;

function verificarAutenticacao() {
  const token = localStorage.getItem('token');
  if (!token) { window.location.href = 'login.html'; return null; }
  return token;
}

async function carregarEventos() {
  const token = verificarAutenticacao();
  if (!token) return;
  try {
    const resp = await fetch(`${API_URL}/eventos`, { headers: { 'Authorization': `Bearer ${token}` }});
    const eventos = await resp.json();
    renderizarEventos(eventos);
    document.getElementById('buscaEvento').addEventListener('input', () => filtrar(eventos));
  } catch (e) {
    console.error(e);
    document.getElementById('tabelaEventos').innerHTML =
      `<tr><td colspan="6" class="text-center text-danger py-3">Erro ao carregar eventos</td></tr>`;
  }
}

function filtrar(eventos) {
  const termo = document.getElementById('buscaEvento').value.toLowerCase();
  const filtrados = eventos.filter(e => !termo || (e.escola || '').toLowerCase().includes(termo));
  renderizarEventos(filtrados);
}

function renderizarEventos(eventos) {
  const tbody = document.getElementById('tabelaEventos');
  if (eventos.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-3">Nenhum evento cadastrado</td></tr>`;
    return;
  }
  tbody.innerHTML = eventos.map(e => `
    <tr>
      <td>${e.id}</td>
      <td>${e.escola}</td>
      <td>${e.tipo_formatura || '-'}</td>
      <td>${e.data_evento ? new Date(e.data_evento).toLocaleDateString('pt-BR') : '-'}</td>
      <td><span class="badge bg-${e.status === 'ativo' ? 'success' : 'secondary'}">${e.status}</span></td>
      <td>
        <button class="btn btn-sm btn-outline-primary" onclick="abrirQRCode(${e.id})">
          <i class="fas fa-qrcode"></i>
        </button>
      </td>
    </tr>`).join('');
}

function abrirQRCode(eventoId) {
  const modal = new bootstrap.Modal(document.getElementById('modalQRCode'));
  const img = document.getElementById('imgQRCode');
  const link = document.getElementById('linkEvento');
  const btnDownload = document.getElementById('btnDownloadQR');

  const qrUrl = `${API_URL}/eventos/${eventoId}/qrcode`;
  const pageUrl = `${window.location.origin}/cadastro?e=${eventoId}`;

  img.src = qrUrl;
  link.textContent = pageUrl;
  link.href = pageUrl;
  btnDownload.onclick = () => baixarArquivo(qrUrl, `evento-${eventoId}.png`);

  modal.show();
}

function baixarArquivo(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function criarEvento() {
  const token = verificarAutenticacao();
  if (!token) return;
  const form = document.getElementById('formNovoEvento');
  const dados = Object.fromEntries(new FormData(form).entries());

  if (!dados.escola || !dados.cidade || !dados.estado) {
    alert('❌ Preencha escola, cidade e estado.');
    return;
  }
  if (dados.estado) dados.estado = dados.estado.trim().toUpperCase().slice(0,2);

  try {
    const resp = await fetch(`${API_URL}/eventos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(dados)
    });
    const json = await resp.json();
    if (!resp.ok) {
      alert(`❌ Erro: ${json.erro || 'Não foi possível criar o evento'}`);
      return;
    }
    alert(`✅ Evento criado! ID: ${json.evento_id}`);
    bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento')).hide();
    form.reset();
    carregarEventos();
  } catch (e) {
    console.error(e);
    alert('❌ Erro de conexão.');
  }
}

document.addEventListener('DOMContentLoaded', carregarEventos);
