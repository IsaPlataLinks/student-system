/* ==================== UI ENHANCEMENTS LIBRARY ====================
   Biblioteca de melhorias de UI para Student System Info
   Versão 1.0 - R3 Formaturas */

const UI = {
  /* ==================== TOAST NOTIFICATIONS ==================== */
  
  mostrarToast(mensagem, tipo = 'success', duracao = 3000) {
    const container = document.getElementById('toastContainer') || this._criarToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast-notificacao toast-${tipo}`;
    
    const icones = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };
    
    const cores = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };
    
    toast.innerHTML = `
      <i class="fas ${icones[tipo]}"></i>
      <span>${mensagem}</span>
    `;
    
    toast.style.cssText = `
      background: ${cores[tipo]};
      color: white;
      padding: 1rem 1.5rem;
      border-radius: 10px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
      margin-bottom: 1rem;
      animation: slideInRight 0.4s ease-out;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      min-width: 250px;
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.4s ease-out';
      setTimeout(() => toast.remove(), 400);
    }, duracao);
  },

  _criarToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
    `;
    document.body.appendChild(container);
    return container;
  },

  /* ==================== RIPPLE EFFECT ==================== */
  
  inicializarRippleEffect() {
    document.querySelectorAll('.ripple-effect').forEach(button => {
      button.addEventListener('click', (e) => {
        const ripple = button.querySelector('.ripple');
        if (!ripple) return;
        
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.animation = 'none';
        
        setTimeout(() => {
          ripple.style.animation = 'rippleAnimation 0.6s ease-out';
        }, 10);
      });
    });
  },

  /* ==================== ETAPAS DO CADASTRO ==================== */
  
  atualizarEtapa(numeroEtapa) {
    const etapas = document.querySelectorAll('.etapa');
    etapas.forEach((etapa, index) => {
      etapa.classList.remove('active', 'completed');
      
      if (index < numeroEtapa - 1) {
        etapa.classList.add('completed');
      } else if (index === numeroEtapa - 1) {
        etapa.classList.add('active');
      }
    });
  },

  marcarEtapaCompleta(numeroEtapa) {
    const etapa = document.querySelector(`[data-etapa="${numeroEtapa}"]`);
    if (etapa) {
      etapa.classList.add('completed');
      etapa.classList.remove('active');
    }
  },

  /* ==================== VALIDAÇÃO COM EFEITO ==================== */
  
  validarCampo(campo) {
    const valor = campo.value.trim();
    const tipo = campo.name;
    let valido = false;
    
    switch(tipo) {
      case 'nome_formando':
      case 'nome_contato':
        valido = valor.length >= 3 && /^[a-zA-ZÀ-ÿ\s']+$/.test(valor);
        break;
      case 'email':
        valido = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
        break;
      case 'whatsapp':
        const digitos = valor.replace(/\D/g, '');
        valido = digitos.length >= 10 && digitos.length <= 11;
        break;
      case 'matricula':
        valido = /^\d{1,10}$/.test(valor.replace(/\s/g, ''));
        break;
      case 'cep':
        valido = !valor || /^\d{5}-\d{3}$/.test(valor);
        break;
      default:
        valido = valor.length > 0;
    }
    
    if (valido) {
      campo.classList.remove('is-invalid');
      campo.classList.add('is-valid');
    } else {
      campo.classList.remove('is-valid');
      campo.classList.add('is-invalid');
    }
    
    return valido;
  },

  /* ==================== CONFETE COM FÍSICA ==================== */
  
  criarConfeteRealista() {
    const cores = ['#F6A21E', '#C57F17', '#FFB84D', '#0D0D0D'];
    const confeteContainer = document.createElement('div');
    confeteContainer.id = 'confete-container';
    confeteContainer.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 9999;
    `;
    document.body.appendChild(confeteContainer);
    
    for (let i = 0; i < 80; i++) {
      setTimeout(() => {
        const confete = document.createElement('div');
        const tamanho = Math.random() * 10 + 4;
        const rotacao = Math.random() * 360;
        const balanco = Math.random() * 100 - 50;
        const duracao = 3000 + Math.random() * 2000;
        const cor = cores[Math.floor(Math.random() * cores.length)];
        
        confete.style.cssText = `
          position: fixed;
          width: ${tamanho}px;
          height: ${tamanho}px;
          background: ${cor};
          top: -20px;
          left: ${Math.random() * 100}%;
          border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
          box-shadow: 0 0 10px rgba(0,0,0,0.1);
          opacity: 1;
          animation: confeteQueda ${duracao}ms linear forwards;
          --balanco: ${balanco}px;
          --rotacao: ${rotacao}deg;
        `;
        confeteContainer.appendChild(confete);
        
        setTimeout(() => confete.remove(), duracao);
      }, i * 25);
    }
    
    // Remover container quando finalizar
    setTimeout(() => {
      if (confeteContainer.children.length === 0) {
        confeteContainer.remove();
      }
    }, 5500);
  },

  /* ==================== ANIMAÇÃO DE DIGITAÇÃO DO NOME ==================== */
  
  animarNome(texto, elementoId = 'nomeExibir') {
    const elemento = document.getElementById(elementoId);
    if (!elemento) return;
    
    let index = 0;
    elemento.textContent = '';
    
    const intervalo = setInterval(() => {
      if (index < texto.length) {
        elemento.textContent += texto[index];
        index++;
      } else {
        clearInterval(intervalo);
      }
    }, 50);
  },

  /* ==================== SHAKE ANIMATION PARA ERROS ==================== */
  
  shakeElement(elemento) {
    elemento.classList.add('error');
    setTimeout(() => {
      elemento.classList.remove('error');
    }, 500);
  },

  /* ==================== LOADING SKELETON ==================== */
  
  criarSkeleton(numeroDePedacos = 3) {
    const container = document.createElement('div');
    
    for (let i = 0; i < numeroDePedacos; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = 'skeleton-box';
      skeleton.style.marginBottom = '0.5rem';
      container.appendChild(skeleton);
    }
    
    return container;
  },

  mostrarSkeleton(elementoId) {
    const elemento = document.getElementById(elementoId);
    if (!elemento) return;
    
    elemento.innerHTML = '';
    elemento.appendChild(this.criarSkeleton(3));
  },

  esconderSkeleton(elementoId) {
    const elemento = document.getElementById(elementoId);
    if (elemento) {
      const skeletons = elemento.querySelectorAll('.skeleton-box');
      skeletons.forEach(sk => sk.remove());
    }
  },

  /* ==================== SPARKLINE MINI GRÁFICOS ==================== */
  
  criarSparkline(canvasId, dados = []) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const altura = canvas.height;
    const largura = canvas.width;
    
    // Valores padrão se não houver dados
    if (dados.length === 0) {
      dados = [20, 30, 25, 35, 40, 30, 35, 45, 40, 50];
    }
    
    const max = Math.max(...dados);
    const min = Math.min(...dados);
    const range = max - min;
    
    ctx.clearRect(0, 0, largura, altura);
    ctx.strokeStyle = '#F6A21E';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    dados.forEach((valor, index) => {
      const x = (index / (dados.length - 1)) * largura;
      const y = altura - ((valor - min) / range) * (altura * 0.8) - altura * 0.1;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
  },

  /* ==================== HOVER EFFECTS ==================== */
  
  adicionarHoverEffect(seletor) {
    const elementos = document.querySelectorAll(seletor);
    elementos.forEach(el => {
      el.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-4px)';
        this.style.boxShadow = '0 8px 20px rgba(246, 162, 30, 0.1)';
      });
      
      el.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.05)';
      });
    });
  },

  /* ==================== FORM HELPERS (MÁSCARAS) ==================== */
  
  mascaraCEP(valor) {
    return valor.replace(/\D/g, '').slice(0, 8).replace(/^(\d{5})(\d{0,3})/, '$1-$2');
  },

  mascaraTelefone(valor) {
    const digitos = valor.replace(/\D/g, '').slice(0, 11);
    
    if (digitos.length <= 10) {
      return digitos.replace(/^(\d{0,2})(\d{0,4})(\d{0,4}).*/, function(_, a, b, c) {
        return (a ? `(${a}` : '') + (a.length === 2 ? ') ' : '') + (b || '') + (b.length === 4 ? '-' : '') + (c || '');
      });
    } else {
      return digitos.replace(/^(\d{0,2})(\d{0,5})(\d{0,4}).*/, function(_, a, b, c) {
        return (a ? `(${a}` : '') + (a.length === 2 ? ') ' : '') + (b || '') + (b.length >= 5 ? '-' : '') + (c || '');
      });
    }
  },

  /* ==================== UTILIDADES ==================== */
  
  removerClasse(elemento, classe) {
    elemento.classList.remove(classe);
  },

  adicionarClasse(elemento, classe) {
    elemento.classList.add(classe);
  },

  toggleClasse(elemento, classe) {
    elemento.classList.toggle(classe);
  },

  /* ==================== VALIDAÇÃO EM TEMPO REAL COM EFEITO ==================== */
  
  validarCampoComEfeito(campo) {
    const valido = this.validarCampo(campo);
    if (!valido) {
      this.shakeElement(campo);
    }
    return valido;
  },

  /* ==================== MODAL COM TRANSIÇÃO ==================== */
  
  abrirModalComTransicao(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.animation = 'zoomIn 0.3s ease-out';
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
  },

  fecharModalComTransicao(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.animation = 'zoomOut 0.3s ease-out';
    setTimeout(() => {
      const bootstrapModal = bootstrap.Modal.getInstance(modal);
      if (bootstrapModal) bootstrapModal.hide();
    }, 150);
  },

  /* ==================== EFEITO DE TRANSIÇÃO DE PÁGINA ==================== */
  
  transicaoPageFadeIn() {
    document.body.style.animation = 'pageTransition 0.5s ease-out';
  },

  /* ==================== INICIALIZAR TUDO ==================== */
  
  inicializar() {
    this.inicializarRippleEffect();
    
    // Validar campos em tempo real
    const campos = document.querySelectorAll('.form-control, .form-select');
    campos.forEach(campo => {
      campo.addEventListener('blur', () => this.validarCampo(campo));
      campo.addEventListener('input', () => {
        if (campo.classList.contains('is-invalid')) {
          this.validarCampo(campo);
        }
      });
    });
    
    // Tooltip Bootstrap
    if (typeof bootstrap !== 'undefined') {
      const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
      tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
      });
    }

    // Transição de página
    this.transicaoPageFadeIn();
  }
};

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => UI.inicializar());
} else {
  UI.inicializar();
}

// Exportar para uso global
window.UI = UI;
