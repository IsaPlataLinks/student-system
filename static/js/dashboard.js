const API_URL = 'http://localhost:5000/api';
let todosAlunos = [];
let alunosFiltrados = [];

// ========== VERIFICAÇÃO DE AUTENTICAÇÃO ==========

function verificarAutenticacao() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }
    return token;
}

// ========== LOGOUT ==========

function logout() {
    if (confirm('Deseja realmente sair?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('nomeUsuario');
        localStorage.removeItem('tipoUsuario');
        window.location.href = 'login.html';
    }
}

// ========== CARREGAR DADOS DO USUÁRIO ==========

function carregarDadosUsuario() {
    const nomeUsuario = localStorage.getItem('nomeUsuario') || 'Usuário';
    const tipoUsuario = localStorage.getItem('tipoUsuario') || 'admin';
    
    document.getElementById('nomeUsuario').textContent = nomeUsuario;
    document.getElementById('tipoUsuario').textContent = 
        tipoUsuario === 'admin' ? 'Administrador' : 'Vendedor';
}

// ========== CARREGAR ALUNOS ==========

async function carregarAlunos() {
    const token = verificarAutenticacao();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/alunos`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
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
        alert('Erro ao conectar com o servidor. Verifique se está rodando.');
    }
}

// ========== RENDERIZAR ALUNOS ==========

function renderizarAlunos(alunos) {
    const container = document.getElementById('alunosGrid');
    
    if (alunos.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="fas fa-inbox"></i>
                <h4>Nenhum aluno encontrado</h4>
                <p>Tente ajustar os filtros de busca ou aguarde novos cadastros.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alunos.map(aluno => `
        <div class="aluno-card">
            <div class="card-header-custom">
                <h6>${aluno.escola || 'Escola não informada'}</h6>
            </div>
            <div class="card-body-custom">
                <div class="foto-container">
                    ${aluno.foto 
                        ? `<img src="${aluno.foto}" alt="${aluno.nome}">`
                        : `<i class="fas fa-user"></i>`
                    }
                </div>
                <div class="info-container">
                    <div class="aluno-nome">${aluno.nome}</div>
                    <div class="aluno-info">
                        <i class="fas fa-chalkboard-teacher"></i>
                        <span>${aluno.turma}</span>
                    </div>
                    <div class="aluno-info">
                        <i class="fas fa-calendar"></i>
                        <span>${aluno.ano_formatura}</span>
                    </div>
                    ${aluno.whatsapp ? `
                        <div class="aluno-info">
                            <i class="fab fa-whatsapp"></i>
                            <span>${aluno.whatsapp}</span>
                        </div>
                    ` : ''}
                    ${aluno.email ? `
                        <div class="aluno-info">
                            <i class="fas fa-envelope"></i>
                            <span>${aluno.email}</span>
                        </div>
                    ` : ''}
                    ${aluno.responsavel ? `
                        <div class="aluno-info">
                            <i class="fas fa-user-tie"></i>
                            <span>${aluno.responsavel}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// ========== ESTATÍSTICAS ==========

function atualizarEstatisticas() {
    // Total de alunos
    document.getElementById('totalAlunos').textContent = todosAlunos.length;

    // Total de escolas únicas
    const escolasUnicas = new Set(todosAlunos.map(a => a.escola).filter(Boolean));
    document.getElementById('totalEscolas').textContent = escolasUnicas.size;

    // Total com fotos
    const comFotos = todosAlunos.filter(a => a.foto).length;
    document.getElementById('totalFotos').textContent = comFotos;
}

// ========== FILTROS ==========

function carregarEscolasNoFiltro() {
    const escolas = [...new Set(todosAlunos.map(a => a.escola).filter(Boolean))];
    const selectEscola = document.getElementById('filtroEscola');
    
    selectEscola.innerHTML = '<option value="">Todas as Escolas</option>' +
        escolas.map(escola => `<option value="${escola}">${escola}</option>`).join('');
}

function aplicarFiltros() {
    const busca = document.getElementById('filtroBusca').value.toLowerCase();
    const escola = document.getElementById('filtroEscola').value;
    const turma = document.getElementById('filtroTurma').value.toLowerCase();
    const ano = document.getElementById('filtroAno').value;

    alunosFiltrados = todosAlunos.filter(aluno => {
        const matchBusca = !busca || aluno.nome.toLowerCase().includes(busca);
        const matchEscola = !escola || aluno.escola === escola;
        const matchTurma = !turma || (aluno.turma && aluno.turma.toLowerCase().includes(turma));
        const matchAno = !ano || aluno.ano_formatura == ano;

        return matchBusca && matchEscola && matchTurma && matchAno;
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

// Aplicar filtros em tempo real na busca por nome
document.addEventListener('DOMContentLoaded', function() {
    const filtroBusca = document.getElementById('filtroBusca');
    if (filtroBusca) {
        filtroBusca.addEventListener('input', aplicarFiltros);
    }
});

// ========== EXPORTAR EXCEL ==========

function exportarExcel() {
    if (alunosFiltrados.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }

    // Criar tabela HTML
    let html = `
        <table>
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Turma</th>
                    <th>Ano</th>
                    <th>Escola</th>
                    <th>Email</th>
                    <th>WhatsApp</th>
                    <th>Responsável</th>
                </tr>
            </thead>
            <tbody>
    `;

    alunosFiltrados.forEach(aluno => {
        html += `
            <tr>
                <td>${aluno.nome}</td>
                <td>${aluno.turma}</td>
                <td>${aluno.ano_formatura}</td>
                <td>${aluno.escola || ''}</td>
                <td>${aluno.email || ''}</td>
                <td>${aluno.whatsapp || ''}</td>
                <td>${aluno.responsavel || ''}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    // Criar Blob e baixar
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `alunos_${new Date().toISOString().split('T')[0]}.xls`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// ========== EVENTOS E QR CODES ==========

async function carregarEventos() {
    const token = verificarAutenticacao();
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/eventos`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            console.error('Erro ao carregar eventos');
            return;
        }

        const eventos = await response.json();
        renderizarEventos(eventos);
    } catch (error) {
        console.error('Erro ao buscar eventos:', error);
    }
}

function renderizarEventos(eventos) {
    const tabela = document.getElementById('tabelaEventos');
    if (!tabela) return; // evita erro caso o HTML não tenha a tabela

    tabela.innerHTML = '';

    if (eventos.length === 0) {
        tabela.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-3">
                    Nenhum evento cadastrado ainda
                </td>
            </tr>
        `;
        return;
    }

    eventos.forEach(evento => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${evento.id}</td>
            <td>${evento.escola}</td>
            <td>${evento.turma_completa}</td>
            <td>${evento.ano_formatura}</td>
            <td>
                <span class="badge bg-${evento.status === 'ativo' ? 'success' : 'secondary'}">
                    ${evento.status}
                </span>
            </td>
            <td>
                <a href="${API_URL}/eventos/${evento.id}/qrcode" 
                   target="_blank" 
                   class="btn btn-sm btn-outline-primary">
                   <i class="fas fa-qrcode"></i> QR
                </a>
            </td>
        `;
        tabela.appendChild(tr);
    });
}

// ========== INICIALIZAÇÃO ==========

document.addEventListener('DOMContentLoaded', function() {
    verificarAutenticacao();
    carregarDadosUsuario();
    carregarAlunos();
    carregarEventos();
});