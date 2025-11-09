const API_URL = `${window.location.origin}/api`;
let todosAlunos = [];
let alunosFiltrados = [];

// ======================================================
// 🔐 AUTENTICAÇÃO E PERFIL
// ======================================================

function verificarAutenticacao() {
  const token = localStorage.getItem('token');
  if (!token) {
    console.warn('Token não encontrado. Redirecionando para login...');
    window.location.href = 'login.html';
    return null;
  }
  
  // Verifica se o token é válido (não vazio)
  if (token.trim() === '' || token === 'undefined' || token === 'null') {
    console.warn('Token inválido. Redirecionando para login...');
    localStorage.removeItem('token');
    window.location.href = 'login.html';
    return null;
  }
  
  return token;
}

function logout() {
  if (confirm('Deseja realmente sair?')) {
    localStorage.removeItem('token');
    localStorage.removeItem('nomeUsuario');
    localStorage.removeItem('tipoUsuario');
    window.location.href = 'login.html';
  }
}

function carregarDadosUsuario() {
  const nomeUsuario = localStorage.getItem('nomeUsuario') || 'Usuário';
  const tipoUsuario = localStorage.getItem('tipoUsuario') || 'admin';
  document.getElementById('nomeUsuario').textContent = nomeUsuario;
  document.getElementById('tipoUsuario').textContent =
    tipoUsuario === 'admin' ? 'Administrador' : 'Vendedor';
}

// ======================================================
// 🛠️ PARSE DE RESPOSTA (à prova de HTML/500)
// ======================================================
async function parseResposta(resp) {
  if (resp.status === 204) return {};
  
  const ct = (resp.headers.get('content-type') || '').toLowerCase();
  const backup = resp.clone(); // ✅ Clone ANTES de qualquer leitura

  // Tenta JSON primeiro
  if (ct.includes('application/json')) {
    try {
      return await resp.json();
    } catch {
      // Falhou JSON, tenta texto no backup
      try {
        const txt = await backup.text();
        return { erro: txt || 'Resposta JSON inválida do servidor.' };
      } catch {
        return { erro: 'Falha ao ler resposta do servidor.' };
      }
    }
  }

  // Não é JSON, lê como texto direto
  try {
    const txt = await resp.text();
    if (!txt.trim()) return {};
    try {
      return JSON.parse(txt); // Tenta parsear se for JSON disfarçado
    } catch {
      return { erro: txt };
    }
  } catch {
    return { erro: 'Falha ao ler resposta do servidor.' };
  }
}

// ======================================================
// 🎓 ALUNOS
// ======================================================

async function carregarAlunos() {
  const token = verificarAutenticacao();
  if (!token) return;

  try {
    const response = await fetch(`${API_URL}/alunos`, {
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

    const payload = await parseResposta(response);

    if (response.ok) {
      todosAlunos = payload;
      alunosFiltrados = [...todosAlunos];
      renderizarAlunos(alunosFiltrados);
      atualizarEstatisticas();
      carregarEscolasNoFiltro();
    } else {
      console.error('Erro ao carregar alunos:', payload.erro || payload);
      alert(`Erro ao carregar alunos: ${payload.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao conectar com o servidor.');
  }
}

function renderizarAlunos(alunos) {
  const container = document.getElementById('alunosGrid');
  if (!container) return;

  if (alunos.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="fas fa-inbox"></i>
        <h4>Nenhum aluno encontrado</h4>
        <p>Tente ajustar os filtros de busca ou aguarde novos cadastros.</p>
      </div>`;
    return;
  }

  container.innerHTML = alunos
    .map(
      (aluno) => `
      <div class="aluno-card" onclick="verDetalhesAluno(${aluno.id})" style="cursor:pointer" title="Clique para ver detalhes completos">
        <div class="card-header-custom">
          <h6>${aluno.escola || 'Escola não informada'}</h6>
        </div>
        <div class="card-body-custom">
          <div class="foto-container">
            ${
              aluno.foto
                ? `<img src="${aluno.foto}" alt="${aluno.nome}">`
                : `<i class="fas fa-user"></i>`
            }
          </div>
          <div class="info-container">
            <div class="aluno-nome">${aluno.nome}</div>
            <div class="aluno-info"><i class="fas fa-chalkboard-teacher"></i><span>${aluno.turma}</span></div>
            <div class="aluno-info"><i class="fas fa-calendar"></i><span>${aluno.ano_formatura || 'N/A'}</span></div>
            ${
              aluno.whatsapp
                ? `<div class="aluno-info"><i class="fab fa-whatsapp"></i><span>${aluno.whatsapp}</span></div>`
                : ''
            }
            ${
              aluno.email
                ? `<div class="aluno-info"><i class="fas fa-envelope"></i><span>${aluno.email}</span></div>`
                : ''
            }
            ${
              aluno.responsavel
                ? `<div class="aluno-info"><i class="fas fa-user-tie"></i><span>${aluno.responsavel}</span></div>`
                : ''
            }
          </div>
        </div>
        <div style="position:absolute;top:10px;right:10px">
          <i class="fas fa-eye text-white" style="opacity:0.7"></i>
        </div>
      </div>`
    )
    .join('');
}

function atualizarEstatisticas() {
  document.getElementById('totalAlunos').textContent = todosAlunos.length;
  const escolasUnicas = new Set(todosAlunos.map((a) => a.escola).filter(Boolean));
  document.getElementById('totalEscolas').textContent = escolasUnicas.size;
  const comFotos = todosAlunos.filter((a) => a.foto).length;
  document.getElementById('totalFotos').textContent = comFotos;
}

// ======================================================
// 🔍 FILTROS
// ======================================================

function carregarEscolasNoFiltro() {
  const escolas = [...new Set(todosAlunos.map((a) => a.escola).filter(Boolean))];
  const selectEscola = document.getElementById('filtroEscola');
  selectEscola.innerHTML =
    '<option value="">Todas as Escolas</option>' +
    escolas.map((e) => `<option value="${e}">${e}</option>`).join('');
}

function aplicarFiltros() {
  const busca = document.getElementById('filtroBusca').value.toLowerCase();
  const escola = document.getElementById('filtroEscola').value;
  const turma = document.getElementById('filtroTurma').value.toLowerCase();
  const ano = document.getElementById('filtroAno').value;

  alunosFiltrados = todosAlunos.filter((a) => {
    return (
      (!busca || a.nome.toLowerCase().includes(busca)) &&
      (!escola || a.escola === escola) &&
      (!turma || (a.turma && a.turma.toLowerCase().includes(turma))) &&
      (!ano || a.ano_formatura == ano)
    );
  });

  renderizarAlunos(alunosFiltrados);
}

function limparFiltros() {
  document.getElementById('filtroBusca').value = '';
  document.getElementById('filtroEscola').value = '';
  document.getElementById('filtroTurma').value = '';
  document.getElementById('filtroAno').value = '';
  alunosFiltrados = [...todosAlunos];
  renderizarAlunos(alunosFiltrados);
}

// ======================================================
// 📁 EXPORTAR EXCEL
// ======================================================

function exportarExcel() {
  if (alunosFiltrados.length === 0) return alert('Não há dados para exportar!');
  
  // Adiciona BOM UTF-8 para corrigir acentuação no Excel
  const BOM = '\uFEFF';
  const html = `${BOM}
    <table>
      <thead><tr><th>Nome</th><th>Turma</th><th>Ano</th><th>Escola</th><th>Email</th><th>WhatsApp</th><th>Responsável</th></tr></thead>
      <tbody>${alunosFiltrados
        .map(
          (a) => `
        <tr>
          <td>${a.nome}</td>
          <td>${a.turma}</td>
          <td>${a.ano_formatura || 'N/A'}</td>
          <td>${a.escola || ''}</td>
          <td>${a.email || ''}</td>
          <td>${a.whatsapp || ''}</td>
          <td>${a.responsavel || ''}</td>
        </tr>`
        )
        .join('')}
      </tbody>
    </table>`;
  const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `alunos_${new Date().toISOString().split('T')[0]}.xls`;
  a.click();
  URL.revokeObjectURL(url);
}

// ======================================================
// 🎟️ EVENTOS E QR CODES
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

    const payload = await parseResposta(response);
    
    if (!response.ok) {
      console.error('Erro ao buscar eventos:', payload.erro || payload);
      alert(`Erro ao carregar eventos: ${payload.erro || 'Erro desconhecido'}`);
      return;
    }
    
    renderizarEventos(payload);
  } catch (err) {
    console.error('Erro ao buscar eventos:', err);
    alert('Erro ao conectar com o servidor.');
  }
}

function renderizarEventos(eventos) {
  const tabela = document.getElementById('tabelaEventos');
  if (!tabela) return;

  tabela.innerHTML =
    eventos.length === 0
      ? `<tr><td colspan="6" class="text-center text-muted py-3">Nenhum evento cadastrado</td></tr>`
      : eventos
          .map(
            (e) => `
        <tr>
          <td>${e.id}</td>
          <td>${e.escola || '-'}</td>
          <td>${e.tipo_formatura || '-'}</td>
          <td>${e.data_evento ? new Date(e.data_evento).toLocaleDateString('pt-BR') : '-'}</td>
          <td><span class="badge bg-${e.status === 'ativo' ? 'success' : 'secondary'}">${e.status}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-primary" onclick="abrirQRCode(${e.id})">
              <i class="fas fa-qrcode"></i> Ver QR
            </button>
          </td>
        </tr>`
          )
          .join('');
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
  btnDownload.onclick = () => baixarQRCode(qrUrl, `evento-${eventoId}.png`);

  modal.show();
}

function baixarQRCode(url, filename) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// ======================================================
// ✅ CRIAR EVENTO
// ======================================================

async function criarEvento() {
  const form = document.getElementById('formNovoEvento');
  const formData = new FormData(form);
  const dados = Object.fromEntries(formData.entries());
  const token = localStorage.getItem('token');

  if (!token) {
    alert('❌ Você precisa fazer login primeiro!');
    window.location.href = 'login.html';
    return;
  }

  if (!dados.escola || !dados.cidade || !dados.estado) {
    alert('❌ Preencha todos os campos obrigatórios!');
    return;
  }

  // Normaliza UF
  if (dados.estado) dados.estado = dados.estado.trim().toUpperCase().slice(0, 2);

  try {
    const response = await fetch(`${API_URL}/eventos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(dados),
    });

    const resultado = await parseResposta(response);

    if (response.ok) {
      alert(`✅ Evento criado com sucesso!\n\nID: ${resultado.evento_id}\nQR Code: ${resultado.qr_url}`);
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento'));
      if (modal) modal.hide();
      form.reset();
      carregarEventos();
    } else {
      console.error('Erro criar evento:', resultado.erro || resultado);
      alert(`❌ Erro: ${resultado.erro || 'Não foi possível criar o evento'}`);
    }
  } catch (error) {
    console.error('❌ Erro na requisição:', error);
    alert('❌ Erro de conexão com o servidor.');
  }
}

// ======================================================
// 👥 LEADS
// ======================================================

// Variáveis globais para edição
let leadAtual = null;
let modoEdicao = false;

// Função para abrir detalhes do aluno (lead)

async function verDetalhesAluno(alunoId) {
  const modal = new bootstrap.Modal(document.getElementById('modalDetalhesLead'));
  const body = document.getElementById('detalhesLeadBody');
  
  body.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin fa-2x"></i><p class="mt-2">Carregando...</p></div>';
  modal.show();

  const token = verificarAutenticacao();
  if (!token) return;

  try {
    const response = await fetch(`${API_URL}/leads/${alunoId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/json',
      },
    });

    if (response.ok) {
      leadAtual = await response.json();
      modoEdicao = false;
      renderizarDetalhesLead();
      
      // Mostrar botão editar
      document.getElementById('btnEditarLead').style.display = 'inline-block';
      document.getElementById('btnSalvarLead').style.display = 'none';
      document.getElementById('btnCancelarEdicao').style.display = 'none';
    } else {
      body.innerHTML = '<div class="alert alert-danger">Erro ao carregar detalhes do lead.</div>';
    }
  } catch (error) {
    console.error('Erro:', error);
    body.innerHTML = '<div class="alert alert-danger">Erro ao conectar com o servidor.</div>';
  }
}

function renderizarDetalhesLead() {
  const body = document.getElementById('detalhesLeadBody');
  const lead = leadAtual;
  
  if (!lead) return;
  
  const fotoHtml = lead.foto 
    ? `<img src="/static/uploads/${lead.foto}" class="img-fluid rounded" style="max-width:150px">`
    : '<i class="fas fa-user-circle fa-5x text-muted"></i>';

  body.innerHTML = `
        <div class="row">
          <div class="col-md-3 text-center mb-3">
            ${fotoHtml}
            <p class="mt-2"><strong>Foto 3x4</strong></p>
          </div>
          <div class="col-md-9">
            <h5 class="mb-3"><i class="fas fa-graduation-cap me-2" style="color:var(--gold)"></i>Dados do Formando</h5>
            <table class="table table-sm table-bordered">
              <tr>
                <th width="150">Nome:</th>
                <td id="tdNomeFormando">${lead.nome_formando}</td>
              </tr>
              <tr>
                <th>Matrícula:</th>
                <td id="tdMatricula">${lead.matricula}</td>
              </tr>
              <tr>
                <th>Série:</th>
                <td id="tdSerie">${lead.serie || '-'}</td>
              </tr>
              <tr>
                <th>Turma:</th>
                <td id="tdTurma">${lead.letra_turma || '-'}</td>
              </tr>
              <tr><th>Tipo Cadastro:</th><td>${lead.tipo_cadastro === 'aluno' ? 'Aluno' : 'Responsável'}</td></tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-user me-2" style="color:var(--gold)"></i>Responsável</h5>
            <table class="table table-sm table-bordered">
              <tr>
                <th width="150">Nome:</th>
                <td id="tdNomeContato">${lead.nome_contato}</td>
              </tr>
              <tr>
                <th>E-mail:</th>
                <td id="tdEmail">${lead.email}</td>
              </tr>
              <tr>
                <th>WhatsApp:</th>
                <td id="tdWhatsapp">${lead.whatsapp || '-'}</td>
              </tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-map-marker-alt me-2" style="color:var(--gold)"></i>Endereço</h5>
            <table class="table table-sm table-bordered">
              <tr><th width="150">CEP:</th><td>${lead.cep || '-'}</td></tr>
              <tr><th>Endereço:</th><td>${lead.endereco || '-'}</td></tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-calendar-check me-2" style="color:var(--gold)"></i>Evento</h5>
            <table class="table table-sm table-bordered">
              <tr><th width="150">Escola:</th><td>${lead.evento?.escola || '-'}</td></tr>
              <tr><th>Tipo:</th><td>${lead.evento?.tipo_formatura || '-'}</td></tr>
              <tr><th>Data:</th><td>${lead.evento?.data_evento ? new Date(lead.evento.data_evento).toLocaleDateString('pt-BR') : '-'}</td></tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-info-circle me-2" style="color:var(--gold)"></i>Informações Adicionais</h5>
            <table class="table table-sm table-bordered">
              <tr><th width="150">Status:</th><td><span class="badge bg-primary">${lead.status_lead}</span></td></tr>
              <tr><th>Cadastrado em:</th><td>${new Date(lead.criado_em).toLocaleString('pt-BR')}</td></tr>
            </table>
          </div>
        </div>
      `;
}

function ativarEdicaoLead() {
  modoEdicao = true;
  const lead = leadAtual;
  
  // Tornar campos editáveis
  document.getElementById('tdNomeFormando').innerHTML = 
    `<input type="text" class="form-control form-control-sm" id="editNomeFormando" value="${lead.nome_formando}">`;
  
  document.getElementById('tdMatricula').innerHTML = 
    `<input type="text" class="form-control form-control-sm" id="editMatricula" value="${lead.matricula}" maxlength="10">`;
  
  document.getElementById('tdSerie').innerHTML = 
    `<select class="form-select form-select-sm" id="editSerie">
      <option value="1º ano" ${lead.serie === '1º ano' ? 'selected' : ''}>1º ano</option>
      <option value="2º ano" ${lead.serie === '2º ano' ? 'selected' : ''}>2º ano</option>
      <option value="3º ano" ${lead.serie === '3º ano' ? 'selected' : ''}>3º ano</option>
      <option value="4º ano" ${lead.serie === '4º ano' ? 'selected' : ''}>4º ano</option>
      <option value="5º ano" ${lead.serie === '5º ano' ? 'selected' : ''}>5º ano</option>
      <option value="6º ano" ${lead.serie === '6º ano' ? 'selected' : ''}>6º ano</option>
      <option value="7º ano" ${lead.serie === '7º ano' ? 'selected' : ''}>7º ano</option>
      <option value="8º ano" ${lead.serie === '8º ano' ? 'selected' : ''}>8º ano</option>
      <option value="9º ano" ${lead.serie === '9º ano' ? 'selected' : ''}>9º ano</option>
      <option value="1º ano EM" ${lead.serie === '1º ano EM' ? 'selected' : ''}>1º ano EM</option>
      <option value="2º ano EM" ${lead.serie === '2º ano EM' ? 'selected' : ''}>2º ano EM</option>
      <option value="3º ano EM" ${lead.serie === '3º ano EM' ? 'selected' : ''}>3º ano EM</option>
    </select>`;
  
  document.getElementById('tdTurma').innerHTML = 
    `<input type="text" class="form-control form-control-sm" id="editTurma" value="${lead.letra_turma || ''}" maxlength="4">`;
  
  document.getElementById('tdNomeContato').innerHTML = 
    `<input type="text" class="form-control form-control-sm" id="editNomeContato" value="${lead.nome_contato}">`;
  
  document.getElementById('tdEmail').innerHTML = 
    `<input type="email" class="form-control form-control-sm" id="editEmail" value="${lead.email}">`;
  
  document.getElementById('tdWhatsapp').innerHTML = 
    `<input type="text" class="form-control form-control-sm" id="editWhatsapp" value="${lead.whatsapp || ''}">`;

  // Alternar botões
  document.getElementById('btnEditarLead').style.display = 'none';
  document.getElementById('btnSalvarLead').style.display = 'inline-block';
  document.getElementById('btnCancelarEdicao').style.display = 'inline-block';
}

function cancelarEdicaoLead() {
  modoEdicao = false;
  renderizarDetalhesLead();
  
  document.getElementById('btnEditarLead').style.display = 'inline-block';
  document.getElementById('btnSalvarLead').style.display = 'none';
  document.getElementById('btnCancelarEdicao').style.display = 'none';
}

async function salvarEdicaoLead() {
  const token = verificarAutenticacao();
  if (!token) return;

  const dadosAtualizados = {
    nome_formando: document.getElementById('editNomeFormando').value.trim(),
    matricula: document.getElementById('editMatricula').value.trim(),
    serie: document.getElementById('editSerie').value,
    letra_turma: document.getElementById('editTurma').value.trim().toUpperCase(),
    nome_contato: document.getElementById('editNomeContato').value.trim(),
    email: document.getElementById('editEmail').value.trim(),
    whatsapp: document.getElementById('editWhatsapp').value.trim(),
  };

  // Validações básicas
  if (!dadosAtualizados.nome_formando || !dadosAtualizados.nome_contato || !dadosAtualizados.email) {
    alert('Preencha todos os campos obrigatórios!');
    return;
  }

  try {
    const response = await fetch(`${API_URL}/leads/${leadAtual.id}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dadosAtualizados),
    });

    if (response.ok) {
      alert('Dados atualizados com sucesso!');
      
      // Atualizar leadAtual com novos dados
      Object.assign(leadAtual, dadosAtualizados);
      
      modoEdicao = false;
      renderizarDetalhesLead();
      
      document.getElementById('btnEditarLead').style.display = 'inline-block';
      document.getElementById('btnSalvarLead').style.display = 'none';
      document.getElementById('btnCancelarEdicao').style.display = 'none';
      
      // Recarregar lista de alunos
      carregarAlunos();
    } else {
      const error = await response.json();
      alert(`Erro ao salvar: ${error.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao conectar com o servidor.');
  }
}

// ======================================================
// 🚀 INICIALIZAÇÃO
// ======================================================

document.addEventListener('DOMContentLoaded', function () {
  verificarAutenticacao();
  carregarDadosUsuario();
  carregarAlunos();
  carregarEventos();

  const filtroBusca = document.getElementById('filtroBusca');
  if (filtroBusca) filtroBusca.addEventListener('input', aplicarFiltros);
});