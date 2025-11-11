const API_URL = `${window.location.origin}/api`;
let todosEventos = [];
let eventosFiltrados = [];

// ======================================================
// 🔐 AUTENTICAÇÃO
// ======================================================

function verificarAutenticacao() {
  const token = localStorage.getItem('token');
  if (!token) {
    console.warn('Token não encontrado. Redirecionando para login...');
    window.location.href = 'login.html';
    return null;
  }
  
  if (token.trim() === '' || token === 'undefined' || token === 'null') {
    console.warn('Token inválido. Redirecionando para login...');
    localStorage.removeItem('token');
    window.location.href = 'login.html';
    return null;
  }
  
  return token;
}

// ======================================================
// 📊 CARREGAR EVENTOS
// ======================================================

async function carregarEventos() {
  const token = verificarAutenticacao();
  if (!token) return;

  try {
    const response = await fetch(`${API_URL}/eventos`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
      },
    });

    if (response.status === 401 || response.status === 422) {
      console.error('Token inválido ou expirado. Status:', response.status);
      alert('Sessão expirada. Faça login novamente.');
      localStorage.removeItem('token');
      window.location.href = 'login.html';
      return;
    }

    if (response.ok) {
      const eventos = await response.json();
      todosEventos = eventos;
      eventosFiltrados = [...todosEventos];
      renderizarEventos(eventosFiltrados);
      
      // Configurar o listener de busca
      const buscaInput = document.getElementById('buscaEvento');
      if (buscaInput) {
        buscaInput.addEventListener('input', (e) => {
          const termo = e.target.value.toLowerCase();
          eventosFiltrados = todosEventos.filter(evento => {
            const escola = (evento.escola || '').toLowerCase();
            const tipo = (evento.tipo_formatura || '').toLowerCase();
            const local = (evento.local_evento || '').toLowerCase();
            return escola.includes(termo) || tipo.includes(termo) || local.includes(termo);
          });
          renderizarEventos(eventosFiltrados);
        });
      }
    } else {
      const error = await response.json();
      console.error('Erro ao carregar eventos:', error);
      alert(`Erro ao carregar eventos: ${error.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao conectar com o servidor.');
  }
}

// ======================================================
// 🎨 RENDERIZAR EVENTOS
// ======================================================

function renderizarEventos(eventos) {
  const tbody = document.getElementById('tabelaEventos');
  
  if (eventos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">
          <i class="fas fa-inbox fa-2x mb-2"></i><br>
          Nenhum evento encontrado
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = eventos.map(e => {
    // Determinar cor do badge baseado no status automático
    let badgeColor = 'secondary';
    let statusTexto = e.status || 'pendente';
    let statusDetalhes = '';
    
    if (e.status === 'ativo') {
      badgeColor = 'success';
      statusDetalhes = e.dias_restantes > 0 ? ` (${e.dias_restantes}d)` : '';
    } else if (e.status === 'finalizado') {
      badgeColor = 'danger';
    } else if (e.status === 'agendado') {
      badgeColor = 'info';
    } else if (e.status === 'pendente') {
      badgeColor = 'warning';
    }
    
    const statusBadge = `<span class="badge bg-${badgeColor}">${statusTexto}${statusDetalhes}</span>`;
    
    const dataFormatada = e.data_evento 
      ? new Date(e.data_evento).toLocaleDateString('pt-BR')
      : 'Não definida';
    
    // Desabilitar botão se QR não for válido
    const btnQR = e.qr_valido 
      ? `<button class="btn-qr" onclick="mostrarQRCode(${e.id}, '${e.escola}', '${e.qr_url}')" title="Ver QR Code">
          <i class="fas fa-qrcode"></i>
        </button>`
      : `<button class="btn-qr" disabled title="QR Code expirado" style="opacity:0.5;cursor:not-allowed">
          <i class="fas fa-ban"></i>
        </button>`;

    return `
      <tr>
        <td>${e.id}</td>
        <td><strong>${e.escola || 'Sem escola'}</strong></td>
        <td>${e.tipo_formatura || '-'}</td>
        <td>${dataFormatada}</td>
        <td>${statusBadge}</td>
        <td class="text-center">${e.total_leads || 0}</td>
        <td class="text-center">${btnQR}</td>
      </tr>
    `;
  }).join('');
}

// ======================================================
// 🔍 BUSCA E FILTROS
// ======================================================

document.getElementById('buscaEvento')?.addEventListener('input', (e) => {
  const termo = e.target.value.toLowerCase();
  
  eventosFiltrados = todosEventos.filter(evento => {
    const escola = (evento.escola || '').toLowerCase();
    const tipo = (evento.tipo_formatura || '').toLowerCase();
    const local = (evento.local_evento || '').toLowerCase();
    
    return escola.includes(termo) || tipo.includes(termo) || local.includes(termo);
  });
  
  renderizarEventos(eventosFiltrados);
});

// ======================================================
// 📥 EXPORTAR EXCEL
// ======================================================

function exportarEventosExcel() {
  if (eventosFiltrados.length === 0) {
    alert('Não há eventos para exportar!');
    return;
  }

  // Adiciona BOM UTF-8 para corrigir acentuação no Excel
  const BOM = '\uFEFF';
  const html = `${BOM}
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Escola</th>
          <th>Cidade</th>
          <th>Estado</th>
          <th>Tipo de Formatura</th>
          <th>Data do Evento</th>
          <th>Local</th>
          <th>Status</th>
          <th>Total de Cadastros</th>
          <th>Link de Cadastro</th>
        </tr>
      </thead>
      <tbody>${eventosFiltrados
        .map(
          (e) => {
            const dataFormatada = e.data_evento 
              ? new Date(e.data_evento).toLocaleDateString('pt-BR')
              : '';
            
            return `
            <tr>
              <td>${e.id}</td>
              <td>${e.escola || ''}</td>
              <td>${e.cidade || ''}</td>
              <td>${e.estado || ''}</td>
              <td>${e.tipo_formatura || ''}</td>
              <td>${dataFormatada}</td>
              <td>${e.local_evento || ''}</td>
              <td>${e.status || ''}</td>
              <td>${e.total_leads || 0}</td>
              <td>${e.qr_url || ''}</td>
            </tr>`;
          }
        )
        .join('')}
      </tbody>
    </table>`;
  
  const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `eventos_${new Date().toISOString().split('T')[0]}.xls`;
  a.click();
  URL.revokeObjectURL(url);
}

// ======================================================
// 📱 QR CODE
// ======================================================

function abrirQRCode(eventoId) {
  const modal = new bootstrap.Modal(document.getElementById('modalQRCode'));
  const img = document.getElementById('imgQRCode');
  const input = document.getElementById('linkEventoInput');
  const btnDownload = document.getElementById('btnDownloadQR');

  const qrUrl = `${API_URL}/eventos/${eventoId}/qrcode`;
  const pageUrl = `${window.location.origin}/cadastro.html?e=${eventoId}`;

  img.src = qrUrl;
  input.value = pageUrl;
  document.getElementById('eventoIdModal').textContent = eventoId;
  
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

function copiarLink() {
  const input = document.getElementById('linkEventoInput');
  input.select();
  document.execCommand('copy');
  
  const btn = event.target.closest('button');
  const iconOriginal = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-check"></i>';
  btn.classList.add('btn-success');
  btn.classList.remove('btn-outline-secondary');
  
  setTimeout(() => {
    btn.innerHTML = iconOriginal;
    btn.classList.remove('btn-success');
    btn.classList.add('btn-outline-secondary');
  }, 1500);
}

function mostrarQRCode(eventoId, nomeEscola, qrUrl) {
  // Compatibilidade com versão anterior
  abrirQRCode(eventoId);
}

// ======================================================
// ➕ CRIAR EVENTO
// ======================================================

async function criarEvento() {
  const token = verificarAutenticacao();
  if (!token) return;

  const form = document.getElementById('formNovoEvento');
  const formData = new FormData(form);
  
  // Validação básica
  if (!formData.get('escola') || !formData.get('cidade') || !formData.get('estado') || 
      !formData.get('tipo_formatura') || !formData.get('local_evento')) {
    alert('Preencha todos os campos obrigatórios!');
    return;
  }

  const data = {
    escola: formData.get('escola'),
    cidade: formData.get('cidade'),
    estado: formData.get('estado').toUpperCase(),
    tipo_formatura: formData.get('tipo_formatura'),
    data_evento: formData.get('data_evento') || null,
    local_evento: formData.get('local_evento'),
  };

  try {
    const response = await fetch(`${API_URL}/eventos`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      alert('Evento criado com sucesso!');
      bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento')).hide();
      form.reset();
      carregarEventos();
    } else {
      const error = await response.json();
      alert(`Erro: ${error.erro || 'Não foi possível criar o evento'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao conectar com o servidor.');
  }
}

// ======================================================
// 🚀 INICIALIZAÇÃO
// ======================================================

document.addEventListener('DOMContentLoaded', () => {
  carregarEventos();
});
