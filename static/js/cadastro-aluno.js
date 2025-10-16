// Configuração da API
const API_URL = 'http://localhost:5000/api';

// ========== MÁSCARAS DE ENTRADA ==========

document.addEventListener('DOMContentLoaded', function() {
    // Máscara WhatsApp
    const inputWhatsApp = document.querySelector('input[name="whatsapp"]');
    if (inputWhatsApp) {
        inputWhatsApp.addEventListener('input', function(e) {
            let valor = e.target.value.replace(/\D/g, '');
            if (valor.length > 11) valor = valor.slice(0, 11);
            
            if (valor.length >= 11) {
                valor = valor.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
            } else if (valor.length >= 7) {
                valor = valor.replace(/(\d{2})(\d{5})/, '($1) $2');
            } else if (valor.length >= 3) {
                valor = valor.replace(/(\d{2})/, '($1) ');
            }
            
            e.target.value = valor;
        });
    }

    // Máscara CEP
    const inputCEP = document.querySelector('input[name="cep"]');
    if (inputCEP) {
        inputCEP.addEventListener('input', function(e) {
            let valor = e.target.value.replace(/\D/g, '');
            if (valor.length > 8) valor = valor.slice(0, 8);
            
            if (valor.length >= 6) {
                valor = valor.replace(/(\d{5})(\d{3})/, '$1-$2');
            }
            
            e.target.value = valor;
        });

        // Buscar endereço pelo CEP (ViaCEP)
        inputCEP.addEventListener('blur', async function() {
            const cep = this.value.replace(/\D/g, '');
            if (cep.length === 8) {
                try {
                    const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
                    const dados = await response.json();
                    
                    if (!dados.erro) {
                        const inputEndereco = document.querySelector('input[name="endereco"]');
                        inputEndereco.value = `${dados.logradouro}, ${dados.bairro}, ${dados.localidade} - ${dados.uf}`;
                    }
                } catch (error) {
                    console.log('Erro ao buscar CEP:', error);
                }
            }
        });
    }

    // Preview da foto
    const inputFoto = document.getElementById('inputFoto');
    const fotoPreview = document.getElementById('fotoPreview');
    
    if (inputFoto) {
        inputFoto.addEventListener('change', function(e) {
            const arquivo = e.target.files[0];
            
            if (arquivo) {
                // Validar tamanho (5MB)
                if (arquivo.size > 5 * 1024 * 1024) {
                    mostrarAlerta('Foto muito grande! Máximo 5MB.', 'danger');
                    e.target.value = '';
                    return;
                }

                // Validar tipo
                if (!['image/jpeg', 'image/jpg', 'image/png'].includes(arquivo.type)) {
                    mostrarAlerta('Formato inválido! Use JPG ou PNG.', 'danger');
                    e.target.value = '';
                    return;
                }

                // Mostrar preview
                const reader = new FileReader();
                reader.onload = function(event) {
                    fotoPreview.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
                };
                reader.readAsDataURL(arquivo);
            }
        });
    }
});

// ========== VALIDAÇÕES ==========

function validarEmail(email) {
    if (!email) return true; // Email é opcional
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function validarWhatsApp(whatsapp) {
    if (!whatsapp) return true; // WhatsApp é opcional
    const regex = /^\(\d{2}\)\s?\d{5}-\d{4}$/;
    return regex.test(whatsapp);
}

function validarCEP(cep) {
    if (!cep) return true; // CEP é opcional
    const regex = /^\d{5}-\d{3}$/;
    return regex.test(cep);
}

// ========== ENVIO DO FORMULÁRIO ==========

const formAluno = document.getElementById('formAluno');
const btnSubmit = document.getElementById('btnSubmit');

formAluno.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Validações
    const email = document.querySelector('input[name="email"]').value;
    const whatsapp = document.querySelector('input[name="whatsapp"]').value;
    const cep = document.querySelector('input[name="cep"]').value;

    if (!validarEmail(email)) {
        mostrarAlerta('E-mail inválido! Verifique o formato.', 'danger');
        return;
    }

    if (!validarWhatsApp(whatsapp)) {
        mostrarAlerta('WhatsApp inválido! Use o formato (XX) XXXXX-XXXX', 'danger');
        return;
    }

    if (!validarCEP(cep)) {
        mostrarAlerta('CEP inválido! Use o formato XXXXX-XXX', 'danger');
        return;
    }

    // Desabilitar botão durante envio
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';

    try {
        // Preparar FormData
        const formData = new FormData(formAluno);

        // Enviar para API
        const response = await fetch(`${API_URL}/cadastro/aluno`, {
            method: 'POST',
            body: formData
        });

        const resultado = await response.json();

        if (response.ok) {
            // Sucesso
            localStorage.setItem('cadastroSucesso', JSON.stringify({
                tipo: 'aluno',
                nome: formData.get('nome'),
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
        mostrarAlerta('Erro de conexão. Verifique sua internet e tente novamente.', 'danger');
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fas fa-check-circle me-2"></i>Finalizar Cadastro';
    }
});

// ========== FUNÇÕES AUXILIARES ==========

function mostrarAlerta(mensagem, tipo) {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${tipo} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.innerHTML = '';
    alertContainer.appendChild(alert);

    // Auto-remover após 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);

    // Scroll para o topo
    window.scrollTo({ top: 0, behavior: 'smooth' });
}