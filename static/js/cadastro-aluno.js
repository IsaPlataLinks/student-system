// Configuração da API
const API_URL = 'http://localhost:5000/api';

// ========== MÁSCARAS E VALIDAÇÕES ==========

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== VALIDAÇÃO DE NOME - Apenas letras (REFORÇADO) =====
    const inputNome = document.querySelector('input[name="nome"]');
    if (inputNome) {
        inputNome.addEventListener('input', function(e) {
            // Remove TUDO que não for letra, espaço ou apóstrofo
            e.target.value = e.target.value.replace(/[^a-zA-ZÀ-ÿ\s']/g, '');
        });
        
        inputNome.addEventListener('keypress', function(e) {
            // Bloqueia a digitação de números
            const char = String.fromCharCode(e.which);
            if (!/[a-zA-ZÀ-ÿ\s']/.test(char)) {
                e.preventDefault();
            }
        });
    }

    // ===== VALIDAÇÃO DE ANO - Máximo 4 dígitos (REFORÇADO) =====
    const inputAno = document.getElementById('inputAno');
    if (inputAno) {
        inputAno.addEventListener('input', function(e) {
            // Remove tudo que não for número
            let valor = e.target.value.replace(/\D/g, '');
            // Limita a 4 dígitos
            if (valor.length > 4) {
                valor = valor.slice(0, 4);
            }
            e.target.value = valor;
        });
        
        inputAno.addEventListener('keypress', function(e) {
            // Bloqueia se já tiver 4 dígitos
            if (this.value.length >= 4) {
                e.preventDefault();
            }
        });
    }

    // ===== CONTADOR DE CARACTERES DA TURMA (aumentado para 30) =====
    const inputTurma = document.getElementById('inputTurma');
    const contadorTurma = document.getElementById('contadorTurma');
    if (inputTurma && contadorTurma) {
        inputTurma.setAttribute('maxlength', '30'); // Aumentado de 20 para 30
        
        inputTurma.addEventListener('input', function(e) {
            contadorTurma.textContent = e.target.value.length;
            
            // Atualiza contador para /30
            const textoContador = document.querySelector('small .text-muted');
            if (textoContador && !textoContador.textContent.includes('/30')) {
                textoContador.innerHTML = '<span id="contadorTurma">0</span>/30 caracteres';
            }
            
            // Alerta visual quando chegar perto do limite
            if (e.target.value.length >= 27) {
                contadorTurma.style.color = 'red';
                contadorTurma.style.fontWeight = 'bold';
            } else {
                contadorTurma.style.color = '';
                contadorTurma.style.fontWeight = '';
            }
        });
    }

    // ===== AUTOCOMPLETE DE ESCOLA + CAMPO "OUTRA" (CORRIGIDO) =====
    const inputEscola = document.getElementById('inputEscola');
    const divOutraEscola = document.getElementById('divOutraEscola');
    const inputOutraEscola = document.getElementById('inputOutraEscola');
    
    if (inputEscola) {
        // Detecta quando digita "Outra escola não listada"
        inputEscola.addEventListener('input', function() {
            if (this.value.toLowerCase().includes('outra') || 
                this.value === 'Outra escola não listada') {
                divOutraEscola.style.display = 'block';
                inputOutraEscola.required = true;
                inputOutraEscola.focus();
            } else {
                divOutraEscola.style.display = 'none';
                inputOutraEscola.required = false;
                inputOutraEscola.value = '';
            }
        });
        
        // Detecta quando seleciona da lista
        inputEscola.addEventListener('change', function() {
            if (this.value === 'Outra escola não listada') {
                divOutraEscola.style.display = 'block';
                inputOutraEscola.required = true;
                inputOutraEscola.focus();
            } else {
                divOutraEscola.style.display = 'none';
                inputOutraEscola.required = false;
                inputOutraEscola.value = '';
            }
        });
        
        // Detecta quando clica na opção
        inputEscola.addEventListener('click', function() {
            if (this.value === 'Outra escola não listada') {
                divOutraEscola.style.display = 'block';
                inputOutraEscola.required = true;
            }
        });
    }

    // ===== MÁSCARA WHATSAPP =====
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

    // ===== MÁSCARA CEP + BUSCA AUTOMÁTICA =====
    const inputCEP = document.getElementById('inputCEP');
    const camposEndereco = document.getElementById('camposEndereco');
    const enderecoManual = document.getElementById('enderecoManual');
    
    if (inputCEP) {
        // Máscara do CEP
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
                // Mostrar loading
                inputCEP.style.borderColor = '#fbbf24';
                inputCEP.disabled = true;
                
                try {
                    const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
                    const dados = await response.json();
                    
                    if (!dados.erro) {
                        // Preencher campos
                        document.getElementById('inputLogradouro').value = dados.logradouro;
                        document.getElementById('inputBairro').value = dados.bairro;
                        document.getElementById('inputCidade').value = dados.localidade;
                        document.getElementById('inputEstado').value = dados.uf;
                        
                        // Mostrar campos de endereço
                        camposEndereco.style.display = 'block';
                        
                        // ESCONDER campo de endereço manual
                        if (enderecoManual) {
                            enderecoManual.style.display = 'none';
                        }
                        
                        // Focar no campo número
                        document.getElementById('inputNumero').focus();
                        
                        // Sucesso visual
                        inputCEP.style.borderColor = '#10b981';
                        setTimeout(() => {
                            inputCEP.style.borderColor = '';
                        }, 2000);
                    } else {
                        mostrarAlerta('CEP não encontrado!', 'warning');
                        inputCEP.style.borderColor = '#ef4444';
                    }
                } catch (error) {
                    console.error('Erro ao buscar CEP:', error);
                    mostrarAlerta('Erro ao buscar CEP. Verifique sua conexão.', 'danger');
                    inputCEP.style.borderColor = '#ef4444';
                } finally {
                    inputCEP.disabled = false;
                }
            }
        });
        
        // Se apagar o CEP, mostrar campo manual novamente
        inputCEP.addEventListener('input', function() {
            if (this.value.length < 9) {
                camposEndereco.style.display = 'none';
                if (enderecoManual) {
                    enderecoManual.style.display = 'block';
                }
            }
        });
    }

    // ===== PREVIEW DA FOTO =====
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

    // Validação de nome (dupla checagem)
    const nome = document.querySelector('input[name="nome"]').value;
    if (!/^[a-zA-ZÀ-ÿ\s']+$/.test(nome)) {
        mostrarAlerta('Nome inválido! Use apenas letras.', 'danger');
        return;
    }

    // Validação de ano (dupla checagem)
    const ano = document.querySelector('input[name="ano_formatura"]').value;
    if (ano.length !== 4 || parseInt(ano) < 2024 || parseInt(ano) > 2035) {
        mostrarAlerta('Ano inválido! Use 4 dígitos entre 2024 e 2035.', 'danger');
        return;
    }

    // Validação de escola
    let escolaFinal = inputEscola.value;
    if (escolaFinal === 'Outra escola não listada') {
        if (!inputOutraEscola.value) {
            mostrarAlerta('Por favor, digite o nome da escola.', 'danger');
            inputOutraEscola.focus();
            return;
        }
        escolaFinal = inputOutraEscola.value;
    }

    // Validações opcionais AGORA SÃO OBRIGATÓRIAS
    const email = document.querySelector('input[name="email"]').value;
    const whatsapp = document.querySelector('input[name="whatsapp"]').value;
    const cep = document.querySelector('input[name="cep"]').value;

    // Email OBRIGATÓRIO
    if (!email) {
        mostrarAlerta('E-mail é obrigatório!', 'danger');
        document.querySelector('input[name="email"]').focus();
        return;
    }

    if (!validarEmail(email)) {
        mostrarAlerta('E-mail inválido! Deve conter @ e .', 'danger');
        document.querySelector('input[name="email"]').focus();
        return;
    }

    // WhatsApp OBRIGATÓRIO
    if (!whatsapp) {
        mostrarAlerta('WhatsApp é obrigatório!', 'danger');
        document.querySelector('input[name="whatsapp"]').focus();
        return;
    }

    if (!validarWhatsApp(whatsapp)) {
        mostrarAlerta('WhatsApp inválido! Use o formato (XX) XXXXX-XXXX', 'danger');
        document.querySelector('input[name="whatsapp"]').focus();
        return;
    }

    // CEP opcional, mas se preenchido deve ser válido
    if (cep && !validarCEP(cep)) {
        mostrarAlerta('CEP inválido! Use o formato XXXXX-XXX', 'danger');
        return;
    }

    // Desabilitar botão durante envio
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';

    try {
        // Preparar FormData
        const formData = new FormData(formAluno);
        
        // Substituir escola se for "Outra"
        if (inputEscola.value === 'Outra escola não listada') {
            formData.set('escola', inputOutraEscola.value);
        }

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