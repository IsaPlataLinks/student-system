const API_URL = `${window.location.origin}/api`;
let todosAlunos = [];
let alunosFiltrados = [];
let sparklineCharts = {};

// ======================================================
// 🖼️ HELPER PARA CONSTRUIR URL DE FOTO
// ======================================================

function construirUrlFoto(foto) {
  if (!foto || typeof foto !== 'string') return null;
  foto = foto.trim();
  if (!foto) return null;
  
  // URL completa (https://res.cloudinary.com/... ou qualquer http)
  if (foto.startsWith('http://') || foto.startsWith('https://')) return foto;
  
  // Caminho relativo (/uploads/...)
  if (foto.startsWith('/')) return foto;
  
  // Apenas nome do arquivo
  return '/uploads/' + foto;
}

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

    console.log('[DEBUG] Renderizando', alunos.length, 'alunos');
    
    container.innerHTML = alunos
      .map(
        (aluno) => {
          const urlFoto = construirUrlFoto(aluno.foto);
          
          console.log(`[DEBUG] Aluno ${aluno.id} (${aluno.nome}): foto="${aluno.foto}" => urlFoto="${urlFoto}"`);
          
          return `
          <div class="aluno-card" onclick="verDetalhesAluno(${aluno.id})" style="cursor:pointer" title="Clique para ver detalhes completos">
          <div class="card-header-custom">
            <h6>${aluno.escola || 'Escola não informada'}</h6>
          </div>
          <div class="card-body-custom">
            <div class="foto-container">
              ${
                urlFoto
                  ? `<img loading="lazy" src="${urlFoto}" 
                           alt="${aluno.nome}" 
                           class="aluno-foto"
                           onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'">
                     <i class="fas fa-user foto-fallback" style="display:none;"></i>`
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
          </div>`;
        }
      )
      .join('');
  }

function atualizarEstatisticas() {
   document.getElementById('totalAlunos').textContent = todosAlunos.length;
   const escolasUnicas = new Set(todosAlunos.map((a) => a.escola).filter(Boolean));
   document.getElementById('totalEscolas').textContent = escolasUnicas.size;
   
   // Buscar contagem correta de fotos da galeria
   carregarContagemFotos();
   
   // Atualizar sparklines
   atualizarSparklines();
}

async function carregarContagemFotos() {
   const token = verificarAutenticacao();
   if (!token) return;
   
   try {
     const response = await fetch(`${API_URL}/dashboard/fotos-count`, {
       headers: {
         Authorization: `Bearer ${token}`,
         Accept: 'application/json',
       },
     });
     
     if (response.ok) {
       const data = await response.json();
       // Usar total_fotos (galeria + leads com foto)
       document.getElementById('totalFotos').textContent = data.total_fotos;
       console.log(`[OK] Fotos contadas: ${data.fotos_galeria} galeria + ${data.leads_com_foto} leads = ${data.total_fotos}`);
     } else {
       console.error('Erro ao contar fotos:', response.status);
     }
   } catch (error) {
     console.error('Erro ao carregar contagem de fotos:', error);
   }
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
      (!escola || (a.escola && a.escola === escola)) &&
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
  
  // Adiciona BOM UTF-8 para corrigir acentuação
  const BOM = '\uFEFF';
  
  const rows = alunosFiltrados.map((a) => [
    a.matricula || 'N/A',
    a.nome,
    a.turma,
    a.ano_formatura || 'N/A',
    a.escola || '',
    a.email || '',
    a.whatsapp || '',
    a.responsavel || ''
  ]);

  const headers = ['Matrícula', 'Nome', 'Turma', 'Ano', 'Escola', 'Email', 'WhatsApp', 'Responsável'];
  
  // Criar TSV (Tab-Separated Values) que Excel interpreta melhor
  const tsv = [headers.join('\t'), ...rows.map(row => row.join('\t'))].join('\n');
  
  const blob = new Blob([BOM + tsv], { type: 'text/plain;charset=utf-8' });
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
    
    // Validar que payload é um array
    if (!Array.isArray(payload)) {
      console.error('Resposta inválida - não é um array:', payload);
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
      ? `<tr><td colspan="7" class="text-center text-muted py-3">Nenhum evento cadastrado</td></tr>`
      : eventos
          .map(
            (e) => {
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
              
              // Desabilitar botão se QR não for válido
              const btnQR = e.qr_valido 
                ? `<button class="btn btn-sm" onclick="abrirQRCode(${e.id})" style="background:var(--gold);color:var(--black);border:none;font-weight:600">
                    <i class="fas fa-qrcode"></i> Ver QR
                  </button>`
                : `<button class="btn btn-sm" disabled style="background:#ccc;color:#666;border:none;opacity:0.6">
                    <i class="fas fa-ban"></i> QR Expirado
                  </button>`;
              
              return `
        <tr>
          <td>${e.id}</td>
          <td>${e.escola || '-'}</td>
          <td>${e.tipo_formatura || '-'}</td>
          <td>${e.data_evento ? new Date(e.data_evento).toLocaleDateString('pt-BR') : '-'}</td>
          <td><span class="badge bg-${badgeColor}">${statusTexto}${statusDetalhes}</span></td>
          <td>${e.total_leads || 0}</td>
          <td>${btnQR}</td>
        </tr>`;
            }
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
      
      // Mostrar botão editar e deletar (apenas se admin)
      document.getElementById('btnEditarLead').style.display = 'inline-block';
      document.getElementById('btnSalvarLead').style.display = 'none';
      document.getElementById('btnCancelarEdicao').style.display = 'none';
      
      // Mostrar botão deletar apenas para admin
      const tipoUsuario = localStorage.getItem('tipoUsuario');
      if (tipoUsuario === 'admin') {
        document.getElementById('btnDeletarLead').style.display = 'inline-block';
      } else {
        document.getElementById('btnDeletarLead').style.display = 'none';
      }
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
   
   const fotoUrl = construirUrlFoto(lead.foto);
   
   const fotoHtml = fotoUrl
     ? `<img src="${fotoUrl}" class="img-fluid rounded" style="max-width:150px; object-fit:cover" 
             onerror="this.style.display='none'; this.parentElement.innerHTML='<i class=\"fas fa-user-circle fa-5x text-muted\"></i>';">`
     : '<i class="fas fa-user-circle fa-5x text-muted"></i>';

  const galeriaHtml = lead.link_galeria 
    ? `<div class="alert mt-2" style="margin-bottom:0;background:rgba(246, 162, 30, 0.1);border:1px solid var(--gold)">
        <i class="fas fa-check-circle me-1" style="color:var(--gold)"></i>
        <strong style="color:var(--gold)">Galeria vinculada!</strong><br>
        <small>${lead.descricao_galeria || 'Link de galeria em nuvem'}</small><br>
        <a href="${lead.link_galeria}" target="_blank" class="btn btn-sm mt-2" style="background:var(--gold);color:var(--black);border:none;font-weight:600">
          <i class="fas fa-external-link-alt me-1"></i>Ver Galeria
        </a>
        <button class="btn btn-sm mt-2" onclick="removerGaleriaLink()" style="background:rgba(0,0,0,0.1);color:var(--black);border:none;font-weight:600">
          <i class="fas fa-trash me-1"></i>Remover
        </button>
      </div>`
    : '';

  body.innerHTML = `
        <div class="row">
          <div class="col-md-3 text-center mb-3">
            ${fotoHtml}
            <p class="mt-2"><strong>Foto 3x4</strong></p>
            <button class="btn btn-sm mt-2 w-100" onclick="abrirUploadFoto()" style="background:var(--gold);color:var(--black);border:none;font-weight:600;transition:all 0.3s ease" onmouseover="this.style.background='var(--gold-dark)'" onmouseout="this.style.background='var(--gold)'">
              <i class="fas fa-cloud-upload-alt me-1"></i>Upload Foto
            </button>
            
            <button class="btn btn-sm mt-2 w-100" onclick="abrirAnexarGaleria()" style="background:var(--gold);color:var(--black);border:none;font-weight:600;transition:all 0.3s ease" onmouseover="this.style.background='var(--gold-dark)'" onmouseout="this.style.background='var(--gold)'">
              <i class="fas fa-cloud me-1"></i>Anexar Galeria
            </button>

            ${galeriaHtml}
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
              <tr><th width="150">Endereço:</th><td>${lead.endereco || '-'}</td></tr>
              <tr><th>CEP:</th><td>${lead.cep || '-'}</td></tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-calendar-check me-2" style="color:var(--gold)"></i>Evento</h5>
            <table class="table table-sm table-bordered">
              <tr><th width="150">Escola:</th><td>${lead.evento?.escola || '-'}</td></tr>
              <tr><th>Tipo:</th><td>${lead.evento?.tipo_formatura || '-'}</td></tr>
              <tr><th>Data:</th><td>${lead.evento?.data_evento ? new Date(lead.evento.data_evento).toLocaleDateString('pt-BR') : '-'}</td></tr>
            </table>

            <h5 class="mt-4 mb-3"><i class="fas fa-info-circle me-2" style="color:var(--gold)"></i>Informações Adicionais</h5>
            <table class="table table-sm table-bordered">
            <tr><th width="150">Status:</th><td id="tdStatusLead"><span class="badge-status ${lead.status_lead}">${lead.status_lead}</span></td></tr>
              <tr><th>Observações:</th><td id="tdObservacoes"><small>${lead.observacoes || '-'}</small></td></tr>
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

  document.getElementById('tdStatusLead').innerHTML = 
    `<select class="form-select form-select-sm" id="editStatusLead">
      <option value="novo" ${lead.status_lead === 'novo' ? 'selected' : ''}>Novo</option>
      <option value="contatado" ${lead.status_lead === 'contatado' ? 'selected' : ''}>Contatado</option>
      <option value="interessado" ${lead.status_lead === 'interessado' ? 'selected' : ''}>Interessado</option>
      <option value="convertido" ${lead.status_lead === 'convertido' ? 'selected' : ''}>Convertido</option>
      <option value="perdido" ${lead.status_lead === 'perdido' ? 'selected' : ''}>Perdido</option>
    </select>`;

  document.getElementById('tdObservacoes').innerHTML = 
    `<textarea class="form-control form-control-sm" id="editObservacoes" maxlength="2000" rows="3" placeholder="Até 2000 caracteres">${lead.observacoes || ''}</textarea>
     <small class="text-muted d-block mt-1"><span id="countObservacoes">0</span>/2000 caracteres</small>`;

  // Contador de caracteres
  document.getElementById('editObservacoes').addEventListener('input', function() {
    document.getElementById('countObservacoes').textContent = this.value.length;
  });

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
    status_lead: document.getElementById('editStatusLead').value,
    observacoes: document.getElementById('editObservacoes').value.trim(),
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
// 📸 UPLOAD DE FOTO
// ======================================================

function previewImagemFoto() {
  const fileInput = document.getElementById('inputFoto');
  const arquivo = fileInput.files[0];
  const preview = document.getElementById('previewFoto');
  const imagemPreview = document.getElementById('imagemPreview');

  if (arquivo) {
    const leitor = new FileReader();
    leitor.onload = function(event) {
      imagemPreview.src = event.target.result;
      preview.style.display = 'block';
    };
    leitor.readAsDataURL(arquivo);
  } else {
    preview.style.display = 'none';
  }
}

function abrirUploadFoto() {
  const modal = new bootstrap.Modal(document.getElementById('modalUploadFoto'));
  modal.show();
}

async function enviarFoto() {
  const token = verificarAutenticacao();
  if (!token) return;

  const fileInput = document.getElementById('inputFoto');
  const arquivo = fileInput.files[0];

  if (!arquivo) {
    alert('Selecione uma foto!');
    return;
  }

  // Validar tipo de arquivo
  const tiposValidos = ['image/jpeg', 'image/png', 'image/jpg'];
  if (!tiposValidos.includes(arquivo.type)) {
    alert('Apenas arquivos JPG, JPEG e PNG são permitidos!');
    return;
  }

  // Validar tamanho (máx 30MB)
  if (arquivo.size > 30 * 1024 * 1024) {
    alert('A foto não pode exceder 30MB!');
    return;
  }

  const formData = new FormData();
  formData.append('foto', arquivo);

  try {
    const response = await fetch(`${API_URL}/leads/${leadAtual.id}/foto`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (response.ok) {
       const resultado = await response.json();
       alert('Foto enviada com sucesso!');
       
       // Atualizar leadAtual com a nova foto
       leadAtual.foto = resultado.foto;
       renderizarDetalhesLead();
       
       // Fechar modal
       const modal = bootstrap.Modal.getInstance(document.getElementById('modalUploadFoto'));
       if (modal) modal.hide();
       
       // Resetar input
       fileInput.value = '';
       
       // Recarregar lista de alunos E estatísticas (com delay para garantir renderização)
       setTimeout(() => {
         carregarAlunos();
         carregarContagemFotos();
       }, 300);
    } else {
      const erro = await response.json();
      alert(`Erro ao enviar foto: ${erro.erro || 'Erro desconhecido'}`);
    }
    } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao conectar com o servidor.');
    }
    }

// ======================================================
// 🗑️ DELETAR LEAD
// ======================================================

function confirmarDelecaoLead() {
  if (!leadAtual) return;
  
  const confirmacao = confirm(
    `⚠️  ATENÇÃO!\n\n` +
    `Tem certeza que deseja deletar o cadastro de ${leadAtual.nome_formando}?\n\n` +
    `Esta ação é IRREVERSÍVEL e todas as informações será perdidas.`
  );
  
  if (confirmacao) {
    deletarLead();
  }
}

async function deletarLead() {
  const token = verificarAutenticacao();
  if (!token) return;
  
  if (!leadAtual) {
    alert('Erro: nenhum lead selecionado');
    return;
  }
  
  const tipoUsuario = localStorage.getItem('tipoUsuario');
  if (tipoUsuario !== 'admin') {
    alert('❌ Apenas administradores podem deletar leads!');
    return;
  }
  
  try {
    const response = await fetch(`${API_URL}/leads/${leadAtual.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (response.ok) {
      alert('✅ Lead deletado com sucesso!');
      
      // Fechar modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalDetalhesLead'));
      if (modal) modal.hide();
      
      // Recarregar lista de alunos
      leadAtual = null;
      carregarAlunos();
    } else {
      const erro = await response.json();
      alert(`❌ Erro ao deletar: ${erro.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro ao deletar lead:', error);
    alert('❌ Erro ao conectar com o servidor.');
  }
}

// ======================================================
// 📊 SPARKLINES
// ======================================================

function gerarDadosSparkline(valor, tipo) {
  // Gera dados simulados para o sparkline baseado no valor
  const baseData = [];
  let variacao = 0;
  
  // Cria uma sequência com tendência
  for (let i = 0; i < 7; i++) {
    const randomVariacao = (Math.random() - 0.5) * 0.3 * valor;
    const ponto = Math.max(0, valor * 0.7 + randomVariacao);
    baseData.push(ponto);
    
    if (i === 6) variacao = ponto - baseData[0];
  }
  
  return {
    dados: baseData,
    variacao: variacao,
    percentual: ((variacao / baseData[0]) * 100).toFixed(1)
  };
}

function criarSparkline(canvasId, valor, tipo) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  
  // Destruir gráfico anterior se existir
  if (sparklineCharts[canvasId]) {
    sparklineCharts[canvasId].destroy();
  }
  
  const dadosSparkline = gerarDadosSparkline(valor, tipo);
  const isPositivo = dadosSparkline.variacao >= 0;
  const cor = isPositivo ? '#10b981' : '#ef4444';
  const corFundo = isPositivo ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
  
  sparklineCharts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom'],
      datasets: [{
        label: tipo,
        data: dadosSparkline.dados,
        borderColor: cor,
        backgroundColor: corFundo,
        borderWidth: 2,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0.4,
        pointBackgroundColor: cor,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        y: {
          display: false,
          beginAtZero: true,
          max: valor * 1.3
        },
        x: {
          display: false
        }
      }
    }
  });
  
  // Atualizar badge de variação
  const badgeId = `variacao-${tipo.toLowerCase()}`;
  const badge = document.getElementById(badgeId);
  if (badge) {
    const percentual = parseFloat(dadosSparkline.percentual);
    const sinal = percentual >= 0 ? '+' : '';
    const classe = percentual >= 0 ? 'positivo' : 'negativo';
    const icon = percentual >= 0 ? 'arrow-up' : 'arrow-down';
    
    badge.className = `stat-variacao ${classe}`;
    badge.innerHTML = `<i class="fas fa-${icon}"></i> ${sinal}${percentual}% esta semana`;
  }
}

function atualizarSparklines() {
  const totalAlunos = todosAlunos.length;
  const escolasUnicas = new Set(todosAlunos.map((a) => a.escola).filter(Boolean)).size;
  const comFotos = todosAlunos.filter((a) => a.foto).length;
  
  criarSparkline('graficoAlunos', Math.max(totalAlunos, 10), 'Alunos');
  criarSparkline('graficoEscolas', Math.max(escolasUnicas, 1), 'Escolas');
  criarSparkline('graficoFotos', Math.max(comFotos, 5), 'Fotos');
}

// ======================================================
// 🚀 INICIALIZAÇÃO
// ======================================================

// ======================================================
// ☁️ GALERIA DE FOTOS EM NUVEM
// ======================================================

function abrirAnexarGaleria() {
  // Se já tem galeria, mostrar aviso
  if (leadAtual && leadAtual.link_galeria) {
    document.getElementById('galeriaAtualInfo').style.display = 'block';
  } else {
    document.getElementById('galeriaAtualInfo').style.display = 'none';
  }
  
  // Limpar campos
  document.getElementById('inputLinkGaleria').value = (leadAtual && leadAtual.link_galeria) ? leadAtual.link_galeria : '';
  document.getElementById('inputDescricaoGaleria').value = (leadAtual && leadAtual.descricao_galeria) ? leadAtual.descricao_galeria : '';
  
  const modal = new bootstrap.Modal(document.getElementById('modalAnexarGaleria'));
  modal.show();
}

async function salvarGaleriaLink() {
  const token = verificarAutenticacao();
  if (!token) return;

  const link = document.getElementById('inputLinkGaleria').value.trim();
  const descricao = document.getElementById('inputDescricaoGaleria').value.trim();

  if (!link) {
    alert('Informe o link da galeria!');
    return;
  }

  if (!link.startsWith('http://') && !link.startsWith('https://')) {
    alert('O link deve começar com http:// ou https://');
    return;
  }

  try {
    const response = await fetch(`${API_URL}/leads/${leadAtual.id}/galeria-link`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        link_galeria: link,
        descricao_galeria: descricao
      }),
    });

    if (response.ok) {
      const resultado = await response.json();
      alert('✅ Galeria anexada com sucesso!');
      
      // Atualizar leadAtual
      leadAtual.link_galeria = resultado.link_galeria;
      leadAtual.descricao_galeria = resultado.descricao_galeria;
      renderizarDetalhesLead();
      
      // Fechar modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalAnexarGaleria'));
      if (modal) modal.hide();
      
      // Recarregar alunos
      carregarAlunos();
    } else {
      const erro = await response.json();
      alert(`❌ Erro: ${erro.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('❌ Erro ao conectar com o servidor.');
  }
}

async function removerGaleriaLink() {
  const confirmacao = confirm('Deseja remover o link da galeria?');
  if (!confirmacao) return;

  const token = verificarAutenticacao();
  if (!token) return;

  try {
    const response = await fetch(`${API_URL}/leads/${leadAtual.id}/galeria-link`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.ok) {
      alert('✅ Galeria removida com sucesso!');
      
      // Atualizar leadAtual
      leadAtual.link_galeria = null;
      leadAtual.descricao_galeria = null;
      renderizarDetalhesLead();
      
      // Recarregar alunos
      carregarAlunos();
    } else {
      const erro = await response.json();
      alert(`❌ Erro: ${erro.erro || 'Erro desconhecido'}`);
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('❌ Erro ao conectar com o servidor.');
  }
}

document.addEventListener('DOMContentLoaded', function () {
  verificarAutenticacao();
  carregarDadosUsuario();
  carregarAlunos();
  carregarEventos();

  const filtroBusca = document.getElementById('filtroBusca');
  if (filtroBusca) filtroBusca.addEventListener('input', aplicarFiltros);
});