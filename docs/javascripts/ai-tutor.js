/*
 * "Aprende con IA": agrega a cada paso (h2/h3) de las páginas de Implementación y Operación un botón que
 * arma un prompt de tutor con el contexto de esa sección, lo copia al portapapeles y abre el cuaderno de
 * NotebookLM del proyecto. Sin dependencias, sin llamadas externas al cargar la página: solo se abre una
 * pestaña cuando el visitante hace clic. El nivel elegido se guarda en sessionStorage (se borra al cerrar la pestaña).
 *
 * NotebookLM no permite pre-cargar la pregunta desde un enlace, por eso el prompt se copia y se pega en el chat.
 * Si NOTEBOOK_URL queda vacío, el botón solo copia el prompt (sirve con cualquier asistente de IA).
 *
 * Medición: cada uso del botón envía a Google Analytics el evento ai_tutor_open (acción, nivel y sección), solo si
 * el visitante aceptó Analytics en el aviso de cookies. Nunca se envía el texto del prompt. La medición automática
 * de Analytics no ve este botón porque abre el cuaderno con window.open y no con un enlace.
 */
(function (root) {
  "use strict";

  // Cuaderno de NotebookLM del proyecto (compartido como "Cualquiera con el enlace", solo lectura).
  var NOTEBOOK_URL = "https://notebook.google.com/notebook/2393c988-484f-4fb3-8cb7-d225ab5a5036";
  var STORAGE_KEY = "aiTutorLevel";
  var MAX_PROMPT = 1500;

  var LEVELS = {
    empezando: {
      label: "Estoy empezando",
      text: "Soy principiante: no asumas conocimientos previos, explica las siglas y usa analogías de la vida diaria."
    },
    intermedio: {
      label: "Intermedio",
      text: "Tengo nivel intermedio: conozco Linux básico; explica lo nuevo sin repetir lo elemental."
    },
    experto: {
      label: "Experto",
      text: "Soy experto: ve directo a las decisiones técnicas, los trade-offs y los casos límite."
    }
  };

  var ACTIONS = {
    explain: {
      label: "Explícamelo",
      text: "Explícame qué hace este paso y por qué hace falta. Empieza por los conceptos previos que necesito, " +
        "con una analogía, y cuando termines hazme una pregunta para comprobar que lo entendí antes de seguir."
    },
    quiz: {
      label: "Hazme un quiz",
      text: "Hazme un cuestionario de 3 preguntas sobre esta sección, de a una, esperando mi respuesta. " +
        "Corrige cada respuesta y explícala con las fuentes."
    },
    help: {
      label: "Algo me falló",
      text: "Algo me falló en este paso. Hazme preguntas para diagnosticarlo (qué comando ejecuté y qué salida vi) " +
        "y guíame con las secciones de fallos de la documentación. Pegaré solo la salida del comando."
    }
  };

  var RULES = "Reglas: responde con las fuentes del cuaderno y dime si algo no está en ellas; avanza de a poco; " +
    "nunca me pidas contraseñas, tokens ni IPs reales.";

  function clean(text) {
    return String(text || "").replace(/\s+/g, " ").replace(/[¶#]+$/, "").trim();
  }

  function buildPrompt(action, level, ctx) {
    var a = ACTIONS[action] || ACTIONS.explain;
    var l = LEVELS[level] || LEVELS.empezando;
    var parts = [
      "Actúa como mi tutor de estudio. Sigo la documentación de un HomeLab (Incus, K3s y GitOps con Argo CD).",
      "Estoy en la página «" + clean(ctx.title) + "», sección «" + clean(ctx.heading) + "» (" + ctx.url + ").",
      l.text,
      a.text,
      RULES
    ];
    var prompt = parts.join("\n\n");
    if (prompt.length > MAX_PROMPT) {
      // Recorta solo el título/sección si hiciera falta; las reglas siempre se conservan.
      var over = prompt.length - MAX_PROMPT;
      var short = clean(ctx.heading).slice(0, Math.max(10, clean(ctx.heading).length - over - 1)) + "…";
      parts[1] = "Estoy en la página «" + clean(ctx.title) + "», sección «" + short + "» (" + ctx.url + ").";
      prompt = parts.join("\n\n").slice(0, MAX_PROMPT);
    }
    return prompt;
  }

  // Páginas donde se activa: Implementación y Operación.
  function isLearningPage(pathname) {
    return /\/(implementacion|operacion)\//.test(pathname);
  }

  /* ---------- DOM (solo en el navegador) ---------- */

  function getLevel() {
    try { return sessionStorage.getItem(STORAGE_KEY) || "empezando"; } catch (e) { return "empezando"; }
  }
  function setLevel(v) {
    try { sessionStorage.setItem(STORAGE_KEY, v); } catch (e) { /* sin almacenamiento: no pasa nada */ }
  }

  function copyText(text) {
    if (root.navigator && navigator.clipboard && root.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy") ? resolve() : reject(new Error("copy")); }
      catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }

  var toast;
  function showToast(prompt, copied) {
    if (!toast) {
      toast = el("div", { "class": "ai-tutor-toast", role: "status", "aria-live": "polite" });
      document.body.appendChild(toast);
    }
    toast.innerHTML = "";
    var msg = copied
      ? (NOTEBOOK_URL ? "Prompt copiado. Pégalo en el chat de NotebookLM (Ctrl/⌘+V)." : "Prompt copiado. Pégalo en tu asistente de IA.")
      : "No pude copiar solo: selecciona el texto y cópialo.";
    toast.appendChild(el("p", { text: msg }));
    var details = el("details", {}, [el("summary", { text: "Ver el prompt" }), el("pre", { text: prompt })]);
    if (!copied) details.setAttribute("open", "");
    toast.appendChild(details);
    toast.appendChild(el("button", { type: "button", "class": "ai-tutor-toast-close", text: "Cerrar" }));
    toast.querySelector(".ai-tutor-toast-close").addEventListener("click", function () { toast.hidden = true; });
    toast.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(function () { if (copied) toast.hidden = true; }, 20000);
  }

  // Evento de Google Analytics. Material crea window.dataLayer y carga gtag solo cuando el visitante acepta la
  // categoría Analytics: sin consentimiento no hay dataLayer y no se envía nada. En localhost lo bloquea la bandera
  // ga-disable de overrides/main.html. GA4 acepta valores de hasta 100 caracteres por parámetro.
  function track(name, params) {
    if (!root.dataLayer || typeof root.dataLayer.push !== "function") return;
    // gtag lee el objeto `arguments`, no un array: por eso la función intermedia.
    (function () { root.dataLayer.push(arguments); })("event", name, params);
  }

  function run(action, heading) {
    var level = getLevel();
    var section = heading.getAttribute("data-ai-heading") || heading.textContent;
    var prompt = buildPrompt(action, level, {
      title: (document.querySelector(".md-content h1") || {}).textContent || document.title,
      heading: section,
      url: location.origin + location.pathname + (heading.id ? "#" + heading.id : "")
    });
    track("ai_tutor_open", {
      ai_action: action,
      ai_level: level,
      ai_section: clean(section).slice(0, 100),
      ai_destination: NOTEBOOK_URL ? "notebooklm" : "clipboard"
    });
    // window.open debe ocurrir dentro del clic para que el navegador no lo bloquee.
    if (NOTEBOOK_URL) root.open(NOTEBOOK_URL, "_blank", "noopener");
    copyText(prompt).then(function () { showToast(prompt, true); }, function () { showToast(prompt, false); });
  }

  function closeMenus(except) {
    document.querySelectorAll(".ai-tutor-menu:not([hidden])").forEach(function (m) {
      if (m !== except) {
        m.hidden = true;
        var b = m.previousElementSibling && m.previousElementSibling.querySelector(".ai-tutor-btn");
        if (b) b.setAttribute("aria-expanded", "false");
      }
    });
  }

  function addButton(heading) {
    heading.setAttribute("data-ai-heading", clean(heading.textContent));
    var btn = el("button", {
      type: "button", "class": "ai-tutor-btn", "aria-haspopup": "true", "aria-expanded": "false",
      "aria-label": "Aprende esto con IA: " + clean(heading.textContent), text: "Aprende con IA"
    });
    var menu = el("div", { "class": "ai-tutor-menu", role: "group", "aria-label": "Aprende esto con IA", hidden: "" });
    Object.keys(ACTIONS).forEach(function (key) {
      var b = el("button", { type: "button", "class": "ai-tutor-action", text: ACTIONS[key].label });
      b.addEventListener("click", function () { run(key, heading); closeMenus(); btn.setAttribute("aria-expanded", "false"); btn.focus(); });
      menu.appendChild(b);
    });
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = menu.hidden;
      closeMenus(open ? menu : null);
      menu.hidden = !open;
      btn.setAttribute("aria-expanded", String(open));
      if (open) menu.querySelector("button").focus();
    });
    heading.appendChild(btn);
    heading.parentNode.insertBefore(menu, heading.nextSibling);
  }

  function addLevelPicker(article) {
    var h1 = article.querySelector("h1");
    if (!h1) return;
    var current = getLevel();
    var group = el("div", { "class": "ai-tutor-level", role: "radiogroup", "aria-label": "Tu nivel para el tutor de IA" });
    group.appendChild(el("span", { "class": "ai-tutor-level-label", text: "Tu nivel para el tutor de IA:" }));
    Object.keys(LEVELS).forEach(function (key) {
      var r = el("button", {
        type: "button", role: "radio", "aria-checked": String(key === current), "class": "ai-tutor-level-opt", text: LEVELS[key].label
      });
      r.addEventListener("click", function () {
        setLevel(key);
        group.querySelectorAll(".ai-tutor-level-opt").forEach(function (o) { o.setAttribute("aria-checked", "false"); });
        r.setAttribute("aria-checked", "true");
      });
      group.appendChild(r);
    });
    group.appendChild(el("a", { "class": "ai-tutor-level-help", href: location.pathname.replace(/\/(implementacion|operacion)\/.*$/, "/aprende/"), text: "¿Cómo funciona?" }));
    h1.parentNode.insertBefore(group, h1.nextSibling);
  }

  // Fuente única de la URL del cuaderno: los enlaces marcados con data-notebook-link (p. ej. el botón de
  // aprende.md) toman su destino de NOTEBOOK_URL. Sin JavaScript conservan su href de respaldo.
  function fillNotebookLinks() {
    if (!NOTEBOOK_URL) return;
    var links = document.querySelectorAll("a[data-notebook-link]");
    for (var i = 0; i < links.length; i++) links[i].setAttribute("href", NOTEBOOK_URL);
  }

  function init() {
    fillNotebookLinks();
    if (!isLearningPage(location.pathname)) return;
    var article = document.querySelector(".md-content article");
    if (!article) return;
    var headings = article.querySelectorAll("h2, h3");
    if (!headings.length) return;
    addLevelPicker(article);
    headings.forEach(function (h) {
      if (h.closest(".admonition, details, .tabbed-set, .card, .stepper")) return;
      // Títulos meta de cada fase: no son pasos que haya que aprender.
      if (/^(objetivo|qué aprendes|stack de esta fase)$/i.test(clean(h.textContent))) return;
      addButton(h);
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".ai-tutor-menu, .ai-tutor-btn")) closeMenus();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenus();
    });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { buildPrompt: buildPrompt, isLearningPage: isLearningPage, LEVELS: LEVELS, ACTIONS: ACTIONS, MAX_PROMPT: MAX_PROMPT };
  } else if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
  }
})(typeof window !== "undefined" ? window : this);
