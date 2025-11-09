// ==================== TOAST NOTIFICATIONS ====================

function mostrarToast(mensagem, tipo = 'success', duracao = 3000) {
  const toastContainer = document.getElementById('toastContainer') || criarToastContainer();
  
  const toast = document.createElement('div');
  toast.className = `toast-notificacao toast-${tipo}`;
  
  const icones = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    warning: 'fa-exclamation-triangle',
    info: 'fa-info-circle'
  };
  
  toast.innerHTML = `
    <i class="fas ${icones[tipo]}"></i>
    <span>${mensagem}</span>
  `;
  
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.4s ease-out';
    setTimeout(() => toast.remove(), 400);
  }, duracao);
}

function criarToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  document.body.appendChild(container);
  return container;
}

// ==================== RIPPLE EFFECT ====================

function inicializarRippleEffect() {
  document.querySelectorAll('.ripple-effect').forEach(button => {
    button.addEventListener('click', function(e) {
      const ripple = this.querySelector('.ripple');
      if (!ripple) return;
      
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.style.animation = 'none';
      
      setTimeout(() => {
        ripple.style.animation = 'ripple-animation 0.6s ease-out';
      }, 10);
    });
  });
}

// ==================== ETAPAS DO CADASTRO ====================

function atualizarEtapa(numeroEtapa) {
  document.querySelectorAll('.etapa').forEach((etapa, index) => {
    etapa.classList.remove('active', 'completed');
    
    if (index < numeroEtapa - 1) {
      etapa.classList.add('completed');
    } else if (index === numeroEtapa - 1) {
      etapa.classList.add('active');
    }
  });
}

function marcarEtapaCompleta(numeroEtapa) {
  const etapa = document.querySelector(`[data-etapa="${numeroEtapa}"]`);
  if (etapa) {
    etapa.classList.add('completed');
    etapa.classList.remove('active');
  }
}

// ==================== VALIDAÇÃO COM EFEITO ==================== 

function validarCampo(campo) {
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
}

// ==================== CONFETE COM FÍSICA ====================

function criarConfeteRealista() {
  const cores = ['#F6A21E', '#C57F17', '#FFB84D', '#0D0D0D'];
  
  for (let i = 0; i < 80; i++) {
    setTimeout(() => {
      const confete = document.createElement('div');
      const tamanho = Math.random() * 10 + 4;
      const velocidade = Math.random() * 3 + 2;
      const rotacao = Math.random() * 360;
      const balanco = Math.random() * 60 - 30;
      const delay = Math.random() * 100;
      
      confete.className = 'confete-particula';
      confete.style.cssText = `
        width: ${tamanho}px;
        height: ${tamanho}px;
        background: ${cores[Math.floor(Math.random() * cores.length)]};
        top: -20px;
        left: ${Math.random() * 100}%;
        border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
      `;
      document.body.appendChild(confete);
      
      confete.animate([
        { 
          transform: `translateY(0) translateX(0) rotate(0deg)`,
          opacity: 1 
        },
        {
          transform: `translateY(${window.innerHeight / 2}px) translateX(${balanco}px) rotate(${rotacao / 2}deg)`,
          opacity: 0.8
        },
        { 
          transform: `translateY(${window.innerHeight + 50}px) translateX(${balanco * 2}px) rotate(${rotacao}deg)`,
          opacity: 0 
        }
      ], {
        duration: 3000 + Math.random() * 2000,
        easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        delay: delay
      }).onfinish = () => confete.remove();
    }, i * 25);
  }
}

// ==================== ANIMAÇÃO DE DIGITAÇÃO DO NOME ====================

function animarNome(texto, elementoId = 'nomeExibir') {
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
}

// ==================== SHAKE ANIMATION PARA ERROS ====================

function shakeElement(elemento) {
  elemento.classList.add('error');
  setTimeout(() => {
    elemento.classList.remove('error');
  }, 500);
}

// ==================== INICIALIZAR TUDO ====================

document.addEventListener('DOMContentLoaded', function() {
  inicializarRippleEffect();
  
  // Validar campos em tempo real
  const campos = document.querySelectorAll('.form-control');
  campos.forEach(campo => {
    campo.addEventListener('blur', () => validarCampo(campo));
    campo.addEventListener('input', () => {
      if (campo.classList.contains('is-invalid')) {
        validarCampo(campo);
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
});

// ==================== UTILITY FUNCTIONS ====================

function removerClasse(elemento, classe) {
  elemento.classList.remove(classe);
}

function adicionarClasse(elemento, classe) {
  elemento.classList.add(classe);
}

function toggleClasse(elemento, classe) {
  elemento.classList.toggle(classe);
}

// ==================== LOADING SKELETON ====================

function criarSkeleton(numeroDePedacos = 3) {
  const container = document.createElement('div');
  
  for (let i = 0; i < numeroDePedacos; i++) {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-box';
    skeleton.style.marginBottom = '0.5rem';
    container.appendChild(skeleton);
  }
  
  return container;
}

function mostrarSkeleton(elementoId) {
  const elemento = document.getElementById(elementoId);
  if (!elemento) return;
  
  elemento.innerHTML = '';
  elemento.appendChild(criarSkeleton(3));
}

function esconderSkeleton(elementoId) {
  const elemento = document.getElementById(elementoId);
  if (elemento) {
    const skeletons = elemento.querySelectorAll('.skeleton-box');
    skeletons.forEach(sk => sk.remove());
  }
}

// ==================== SPARKLINE MINI GRÁFICOS ====================

function criarSparkline(canvasId, dados = []) {
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
}

// ==================== HOVER EFFECTS ====================

function adicionarHoverEffect(seletor) {
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
}

// ==================== FORM HELPERS ====================

function mascaraCEP(valor) {
  return valor.replace(/\D/g, '').slice(0, 8).replace(/^(\d{5})(\d{0,3})/, '$1-$2');
}

function mascaraTelefone(valor) {
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
}

// Exporte para uso global
window.UI = {
  mostrarToast,
  validarCampo,
  atualizarEtapa,
  marcarEtapaCompleta,
  criarConfeteRealista,
  animarNome,
  shakeElement,
  inicializarRippleEffect,
  criarSkeleton,
  mostrarSkeleton,
  esconderSkeleton,
  criarSparkline,
  adicionarHoverEffect,
  mascaraCEP,
  mascaraTelefone
};
