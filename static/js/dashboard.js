const API_URL = `${window.location.origin}/api`;
let todosAlunos = [];
let alunosFiltrados = [];

// ======================================================
// 🔐 AUTENTICAÇÃO E PERFIL
// ======================================================

function verificarAutenticacao() {
    const token = localStorage.getItem('token');
    if (!token) {
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
// 🎓 ALUNOS
// ======================================================

async function carregarAlunos() {
    const token = verificarAutenticacao();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/alunos`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401) {
            alert('Sessão expirada. Faça login novamente.');
            logout();
            return;
        }

        if (response.ok) {
            todosAlunos = await response.json();
            alunosFiltrados = [...todosAlunos];
            renderizarAlunos(alunosFiltrados);
            atualizarEstatisticas();
            carregarEscolasNoFiltro();
        } else {
            console.error('Erro ao carregar alunos');
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

    container.innerHTML = alunos.map(aluno => `
        <div class="aluno-card">
            <div class="card-header-custom">
                <h6>${aluno.escola || 'Escola não informada'}</h6>
            </div>
            <div class="card-body-custom">
                <div class="foto-container">
                    ${aluno.foto ? `<img src="${aluno.foto}" alt="${aluno.nome}">` : `<i class="fas fa-user"></i>`}
                </div>
                <div class="info-container">
                    <div class="aluno-nome">${aluno.nome}</div>
                    <div class="aluno-info"><i class="fas fa-chalkboard-teacher"></i><span>${aluno.turma}</span></div>
                    <div class="aluno-info"><i class="fas fa-calendar"></i><span>${aluno.ano_formatura}</span></div>
                    ${aluno.whatsapp ? `<div class="aluno-info"><i class="fab fa-whatsapp"></i><span>${aluno.whatsapp}</span></div>` : ''}
                    ${aluno.email ? `<div class="aluno-info"><i class="fas fa-envelope"></i><span>${aluno.email}</span></div>` : ''}
                    ${aluno.responsavel ? `<div class="aluno-info"><i class="fas fa-user-tie"></i><span>${aluno.responsavel}</span></div>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

function atualizarEstatisticas() {
    document.getElementById('totalAlunos').textContent = todosAlunos.length;
    const escolasUnicas = new Set(todosAlunos.map(a => a.escola).filter(Boolean));
    document.getElementById('totalEscolas').textContent = escolasUnicas.size;
    const comFotos = todosAlunos.filter(a => a.foto).length;
    document.getElementById('totalFotos').textContent = comFotos;
}

// ======================================================
// 🔍 FILTROS
// ======================================================

function carregarEscolasNoFiltro() {
    const escolas = [...new Set(todosAlunos.map(a => a.escola).filter(Boolean))];
    const selectEscola = document.getElementById('filtroEscola');
    selectEscola.innerHTML = '<option value="">Todas as Escolas</option>' +
        escolas.map(e => `<option value="${e}">${e}</option>`).join('');
}

function aplicarFiltros() {
    const busca = document.getElementById('filtroBusca').value.toLowerCase();
    const escola = document.getElementById('filtroEscola').value;
    const turma = document.getElementById('filtroTurma').value.toLowerCase();
    const ano = document.getElementById('filtroAno').value;

    alunosFiltrados = todosAlunos.filter(a => {
        return (!busca || a.nome.toLowerCase().includes(busca)) &&
               (!escola || a.escola === escola) &&
               (!turma || (a.turma && a.turma.toLowerCase().includes(turma))) &&
               (!ano || a.ano_formatura == ano);
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
    const html = `
        <table>
            <thead><tr><th>Nome</th><th>Turma</th><th>Ano</th><th>Escola</th><th>Email</th><th>WhatsApp</th><th>Responsável</th></tr></thead>
            <tbody>${alunosFiltrados.map(a => `
                <tr>
                    <td>${a.nome}</td>
                    <td>${a.turma}</td>
                    <td>${a.ano_formatura}</td>
                    <td>${a.escola || ''}</td>
                    <td>${a.email || ''}</td>
                    <td>${a.whatsapp || ''}</td>
                    <td>${a.responsavel || ''}</td>
                </tr>`).join('')}
            </tbody>
        </table>`;
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
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
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const eventos = await response.json();
        renderizarEventos(eventos);
    } catch (err) {
        console.error('Erro ao buscar eventos:', err);
        alert('Erro ao carregar eventos. Verifique sua conexão.');
    }
}

function renderizarEventos(eventos) {
    const tabela = document.getElementById('tabelaEventos');
    if (!tabela) return;

    tabela.innerHTML = eventos.length === 0
        ? `<tr><td colspan="6" class="text-center text-muted py-3">Nenhum evento cadastrado</td></tr>`
        : eventos.map(e => `
            <tr>
                <td>${e.id}</td>
                <td>${e.escola}</td>
                <td>${e.tipo_formatura || '-'}</td>
                <td>${e.data_evento ? new Date(e.data_evento).toLocaleDateString('pt-BR') : '-'}</td>
                <td><span class="badge bg-${e.status === 'ativo' ? 'success' : 'secondary'}">${e.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="abrirQRCode(${e.id})">
                        <i class="fas fa-qrcode"></i> Ver QR
                    </button>
                </td>
            </tr>
        `).join('');
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

function abrirModalNovoEvento() {
    const modal = new bootstrap.Modal(document.getElementById('modalNovoEvento'));
    modal.show();
}


// ======================================================
// 🚀 INICIALIZAÇÃO
// ======================================================

document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacao();
    carregarDadosUsuario();
    carregarAlunos();
    carregarEventos();

    const filtroBusca = document.getElementById('filtroBusca');
    if (filtroBusca) filtroBusca.addEventListener('input', aplicarFiltros);
});

async function criarEvento() {
    const form = document.getElementById('formNovoEvento');
    const formData = new FormData(form);
    const dados = Object.fromEntries(formData.entries());
    const token = localStorage.getItem('token');

    // ✅ Validação básica
    if (!dados.escola || !dados.cidade || !dados.estado) {
        alert('❌ Preencha todos os campos obrigatórios!');
        return;
    }

    // ✅ Log para debug
    console.log('📤 Enviando dados:', dados);
    console.log('🔑 Token:', token ? 'presente' : 'ausente');

    try {
        const response = await fetch(`${API_URL}/eventos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(dados)
        });

        console.log('📥 Status da resposta:', response.status);
        const resultado = await response.json();
        console.log('📥 Resposta completa:', resultado);

        if (response.ok) {
            alert(`✅ Evento criado com sucesso!\n\nID: ${resultado.evento_id}\nQR Code: ${resultado.qr_url}`);
            
            // Fecha o modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalNovoEvento'));
            modal.hide();
            
            // Limpa o formulário
            form.reset();
            
            // Recarrega a lista de eventos
            carregarEventos();
            
        } else {
            alert(`❌ Erro: ${resultado.erro || 'Não foi possível criar o evento'}`);
        }

    } catch (error) {
        console.error('❌ Erro na requisição:', error);
        alert('❌ Erro de conexão com o servidor.');
    }
}
