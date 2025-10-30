// ==================== CONFIGURAÇÃO ====================
const API_URL = 'http://localhost:5000/api';

// ==================== ELEMENTOS ====================
const loading = document.getElementById('loading');
const boasVindas = document.getElementById('boasVindas');
const formulario = document.getElementById('formulario');
const formCadastro = document.getElementById('formCadastro');
const alertContainer = document.getElementById('alertContainer');
const btnSubmit = document.getElementById('btnSubmit');

const inputMatricula = document.getElementById('inputMatricula');
const inputNomeFormando = document.getElementById('inputNomeFormando');
const inputNomeContato = document.getElementById('inputNomeContato');
const inputEmail = document.getElementById('inputEmail');
const inputWhatsApp = document.getElementById('inputWhatsApp');
const inputFoto = document.getElementById('inputFoto');
const fotoPreview = document.getElementById('fotoPreview');

// ==================== INICIALIZAÇÃO ====================
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const eventoId = urlParams.get('e');
    
    if (!eventoId) {
        loading.classList.remove('show');
        mostrarAlerta('Link inválido! Entre em contato com a R3 Formaturas.', 'danger');
        return;
    }
    
    document.getElementById('eventoId').value = eventoId;
    carregarEvento(eventoId);
});

// ==================== CARREGAR EVENTO ====================
async function carregarEvento(eventoId) {
    try {
        const response = await fetch(`${API_URL}/eventos/${eventoId}`);
        
        if (!response.ok) {
            throw new Error('Evento não encontrado');
        }
        
        const evento = await response.json();
        
        // Mostrar informações do evento
        document.getElementById('eventoTitulo').textContent = 
            `Formatura ${evento.tipo_formatura} ${evento.ano_formatura}`;
        document.getElementById('eventoDetalhes').innerHTML = `
            <i class="fas fa-school me-2"></i><strong>${evento.escola.nome}</strong><br>
            <i class="fas fa-users me-2"></i>Turma: ${evento.turma_completa}
        `;
        
        // Mostrar boas-vindas
        loading.classList.remove('show');
        boasVindas.style.display = 'block';
        
    } catch (error) {
        loading.classList.remove('show');
        mostrarAlerta('Erro ao carregar evento. Verifique o link.', 'danger');
        console.error('Erro:', error);
    }
}

// ==================== INICIAR CADASTRO ====================
function iniciarCadastro() {
    boasVindas.style.display = 'none';
    formulario.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    inicializarValidacoes();
}

// ==================== SELEÇÃO DE TIPO ====================
function selecionarTipo(tipo) {
    document.querySelectorAll('.tipo-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    const tipoOption = tipo === 'aluno' ? 
        document.getElementById('tipoAluno').parentElement : 
        document.getElementById('tipoResponsavel').parentElement;
    
    tipoOption.classList.add('selected');
    document.getElementById(tipo === 'aluno' ? 'tipoAluno' : 'tipoResponsavel').checked = true;
}

// ==================== VALIDAÇÕES EM TEMPO REAL ====================
function inicializarValidacoes() {
    // Validar matrícula
    inputMatricula.addEventListener('input', function(e) {
        let valor = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        e.target.value = valor;
        
        const valido = valor.length >= 3;
        validarCampo(e.target, valido, 'matricula');
    });

    // Validar nome do formando
    inputNomeFormando.addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/[^a-zA-ZÀ-ÿ\s']/g, '');
        const valido = e.target.value.trim().length >= 3;
        validarCampo(e.target, valido, 'nomeFormando');
    });

    // Validar nome do contato
    inputNomeContato.addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/[^a-zA-ZÀ-ÿ\s']/g, '');
        const valido = e.target.value.trim().length >= 3;
        validarCampo(e.target, valido, 'nomeContato');
    });

    // Validar e-mail
    inputEmail.addEventListener('blur', function(e) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const valido = regex.test(e.target.value);
        validarCampo(e.target, valido, 'email');
    });

    // Máscara WhatsApp
    inputWhatsApp.addEventListener('input', function(e) {
        let valor = e.target.value.replace(/\D/g, '');
        
        if (valor.length <= 11) {
            if (valor.length <= 2) {
                valor = valor.replace(/^(\d{0,2})/, '($1');
            } else if (valor.length <= 7) {
                valor = valor.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
            } else {
                valor = valor.replace(/^(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
            }
        }
        
        e.target.value = valor;
        
        const valido = valor.replace(/\D/g, '').length === 11;
        validarCampo(e.target, valido, 'whatsapp');
    });

    // Preview foto
    inputFoto.addEventListener('change', function(e) {
        const file = e.target.files[0];
        
        if (file) {
            // Validar tamanho
            if (file.size > 5 * 1024 * 1024) {
                mostrarAlerta('Foto muito grande! Máximo 5MB.', 'danger');
                e.target.value = '';
                return;
            }

            // Validar tipo
            if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
                mostrarAlerta('Formato inválido! Use JPG ou PNG.', 'danger');
                e.target.value = '';
                return;
            }

            // Mostrar preview
            const reader = new FileReader();
            reader.onload = function(event) {
                fotoPreview.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
                fotoPreview.classList.add('has-image');
                
                const btnRemove = document.createElement('button');
                btnRemove.type = 'button';
                btnRemove.className = 'foto-remove-btn';
                btnRemove.innerHTML = '<i class="fas fa-times"></i>';
                btnRemove.onclick = function(e) {
                    e.stopPropagation();
                    removerFoto();
                };
                fotoPreview.appendChild(btnRemove);
            };
            reader.readAsDataURL(file);
        }
    });
}

function validarCampo(input, isValid, id) {
    const validIcon = document.getElementById(`${id}Valid`);
    const invalidIcon = document.getElementById(`${id}Invalid`);

    if (isValid) {
        validIcon.classList.add('show');
        invalidIcon.classList.remove('show');
    } else if (input.value.length > 0) {
        invalidIcon.classList.add('show');
        validIcon.classList.remove('show');
    } else {
        validIcon.classList.remove('show');
        invalidIcon.classList.remove('show');
    }
}

function removerFoto() {
    inputFoto.value = '';
    fotoPreview.classList.remove('has-image');
    fotoPreview.innerHTML = `
        <div class="placeholder">
            <i class="fas fa-camera fa-2x mb-2"></i>
            <p class="mb-0" style="font-size: 0.9rem;">Clique para adicionar</p>
        </div>
    `;
}

// ==================== SUBMIT ====================
formCadastro.addEventListener('submit', async function(e) {
    e.preventDefault();

    const matricula = inputMatricula.value.trim();
    const nomeFormando = inputNomeFormando.value.trim();
    const nomeContato = inputNomeContato.value.trim();
    const email = inputEmail.value.trim();
    const whatsapp = inputWhatsApp.value.trim();
    const tipoCadastro = document.querySelector('input[name="tipo_cadastro"]:checked');

    // Validações
    if (!tipoCadastro) {
        mostrarAlerta('Selecione se você é aluno ou responsável!', 'warning');
        return;
    }

    if (matricula.length < 3) {
        mostrarAlerta('Matrícula inválida! Digite pelo menos 3 caracteres.', 'danger');
        inputMatricula.focus();
        return;
    }

    if (nomeFormando.length < 3) {
        mostrarAlerta('Nome do formando inválido!', 'danger');
        inputNomeFormando.focus();
        return;
    }

    if (nomeContato.length < 3) {
        mostrarAlerta('Seu nome inválido!', 'danger');
        inputNomeContato.focus();
        return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        mostrarAlerta('E-mail inválido!', 'danger');
        inputEmail.focus();
        return;
    }

    if (whatsapp.replace(/\D/g, '').length !== 11) {
        mostrarAlerta('WhatsApp inválido! Use o formato (11) 98765-4321', 'danger');
        inputWhatsApp.focus();
        return;
    }

    // Desabilitar botão
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Cadastrando...';

    try {
        const formData = new FormData(formCadastro);

        const response = await fetch(`${API_URL}/cadastro`, {
            method: 'POST',
            body: formData
        });

        const resultado = await response.json();

        if (response.ok) {
            // Sucesso
            localStorage.setItem('cadastroSucesso', JSON.stringify({
                tipo: tipoCadastro.value,
                nome: nomeFormando,
                matricula: matricula,
                id: resultado.id
            }));
            window.location.href = 'sucesso.html';
        } else {
            // Erro
            mostrarAlerta(resultado.erro || 'Erro ao cadastrar. Tente novamente.', 'danger');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fas fa-check-circle me-2"></i>Finalizar Cadastro';
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarAlerta('Erro de conexão. Verifique sua internet.', 'danger');
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fas fa-check-circle me-2"></i>Finalizar Cadastro';
    }
});

// ==================== ALERTAS ====================
function mostrarAlerta(mensagem, tipo) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${tipo} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 5000);

    window.scrollTo({ top: 0, behavior: 'smooth' });
}