// MovementMonitor — módulo isolado
// Recebe keypoints, devolve classificação. Não conhece TensorFlow.
var MovementMonitor = (function() {
  "use strict";
  var CONFIG = null;         // carregado de movement-config.json
  var frames = [];           // ring buffer
  var estadoAtual = 0;
  var eventos = [];

  async function carregarConfig(url) {
    var resp = await fetch(url || "/movement-config.json", { cache: "no-store" });
    CONFIG = await resp.json();
  }

  function push(frame) {
    // frame: { ts, keypoints, width, height }
    frames.push(frame);
    if (frames.length > CONFIG.janela.frames_maximo) frames.shift();
    return analisar();
  }

  function analisar() {
    if (!CONFIG || frames.length < CONFIG.janela.frames_minimo_para_decisao) {
      return { estado: 0, score: 0, motivo: "aguardando_dados" };
    }

    var score = 0;
    var motivos = [];

    // 1. Direção do quadril (peso 3)
    var dir = calcularDirecaoQuadril();
    if (dir === "desce") { score += 3; motivos.push("quadril_desce"); }
    else if (dir === "sobe") { /* contexto normal */ }
    else { score += 0; }

    // 2. Velocidade de queda (peso 2)
    var vel = calcularVelocidadeQueda();
    if (vel >= CONFIG.sinais.velocidade_queda_quadril.limiar_critico) { score += 2; motivos.push("velocidade_critica"); }
    else if (vel >= CONFIG.sinais.velocidade_queda_quadril.limiar_suspeito) { score += 1; motivos.push("velocidade_suspeita"); }

    // 3. Ângulo do tronco (peso 2)
    var ang = calcularAnguloMaximo();
    if (ang >= CONFIG.sinais.angulo_tronco.limiar_critico_graus) { score += 2; motivos.push("angulo_critico"); }
    else if (ang >= CONFIG.sinais.angulo_tronco.limiar_suspeito_graus) { score += 1; motivos.push("angulo_suspeito"); }

    // 4. Persistência do ângulo (peso 2)
    var persAng = calcularPersistenciaAngulo();
    if (persAng >= CONFIG.sinais.persistencia_angulo.tempo_critico_segundos) { score += 2; motivos.push("angulo_persistente"); }

    // 5. Persistência baixa (peso 3)
    var persBaixa = calcularPersistenciaBaixa();
    if (persBaixa >= CONFIG.sinais.persistencia_baixa.tempo_critico_segundos) { score += 3; motivos.push("quadril_baixo_persistente"); }
    else if (persBaixa >= CONFIG.sinais.persistencia_baixa.tempo_minimo_segundos) { score += 2; motivos.push("quadril_baixo"); }

    // 6. Perda de tracking (peso 1)
    if (detectarPerdaTracking()) { score += 1; motivos.push("perda_tracking"); }

    // Contexto: se quadril sobe, reduz metade
    if (dir === "sobe" && CONFIG.contexto.reduzir_score_se_quadril_sobe) {
      score = Math.round(score * CONFIG.contexto.fator_reducao_contexto_normal);
    }

    // Classificação
    var est = 0;
    if (score >= CONFIG.classificacao.estagio_2_verificar.score_minimo) est = 2;
    else if (score >= CONFIG.classificacao.estagio_1_observar.score_minimo) est = 1;

    if (est !== estadoAtual) {
      eventos.push({ ts: Date.now(), de: estadoAtual, para: est, score: score, motivos: motivos });
      estadoAtual = est;
    }

    return {
      estado: est,
      score: score,
      motivos: motivos,
      direcao_quadril: dir,
      mensagem: est === 2 ? CONFIG.mensagens.estagio_2 : null
    };
  }

  // --- Funções internas (implementação detalhada na próxima etapa) ---
  function calcularDirecaoQuadril() { /* ... */ }
  function calcularVelocidadeQueda() { /* ... */ }
  function calcularAnguloMaximo() { /* ... */ }
  function calcularPersistenciaAngulo() { /* ... */ }
  function calcularPersistenciaBaixa() { /* ... */ }
  function detectarPerdaTracking() { /* ... */ }

  return {
    carregarConfig: carregarConfig,
    push: push,
    getEstado: function() { return estadoAtual; },
    getEventos: function() { return eventos.slice(); },
    reset: function() { frames = []; estadoAtual = 0; }
  };
})();
