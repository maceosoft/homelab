# Aprende con IA (gratis)

Este HomeLab está pensado para que aprendas mientras lo construyes. Junto a cada paso de la guía hay un botón
**Aprende con IA** que prepara una pregunta de tutor con el contexto de esa sección y te lleva a un cuaderno de
estudio que **solo responde con esta documentación**. Todo lo que se usa aquí es gratuito.

## Cómo se usa, en tres pasos

1. **Elige tu nivel** en la barra que aparece bajo el título de cada página de la guía: *Estoy empezando*,
   *Intermedio* o *Experto*. Cambia cómo te explica la inteligencia artificial (IA): desde analogías cotidianas
   hasta decisiones técnicas.
2. **Pulsa «Aprende con IA»** junto al título del paso en que estás y elige: **Explícamelo**, **Hazme un quiz**
   o **Algo me falló**. El sitio copia la pregunta y abre el cuaderno en otra pestaña.
3. **Pega la pregunta** en el chat del cuaderno (`Ctrl+V`, o `⌘+V` en Mac) y conversa.

!!! note "¿Por qué hay que pegar?"
    NotebookLM no permite abrir un cuaderno con la pregunta ya escrita desde un enlace. Por eso el botón copia el
    texto y tú lo pegas: un paso extra, pero funciona siempre.

## El cuaderno de estudio (NotebookLM)

[**Abrir el cuaderno del HomeLab**](https://notebooklm.google/){ .md-button data-notebook-link="1" }

Es un cuaderno de [NotebookLM](https://notebooklm.google/) con toda esta documentación como fuente. Responde solo con
ella y cita de dónde sale cada respuesta, así que es difícil que se invente cosas. Además de conversar, puedes pedirle:

- una **guía de estudio** de una fase;
- un **cuestionario** o **tarjetas de repaso** con explicación de cada respuesta;
- un **resumen en audio** para escuchar mientras haces otra cosa;
- un **mapa mental** de cómo se conectan las piezas.

**Lo que conviene saber (plan gratuito):**

- Necesitas una **cuenta de Google**.
- Cada cuenta tiene un límite diario (hoy: unas 50 preguntas de chat y 3 resúmenes en audio por día).
- El cuaderno lo mantiene el equipo del proyecto; si la guía cambió hace poco, puede tardar en ponerse al día.

## Si no quieres usar NotebookLM

El botón siempre **copia la pregunta**, así que puedes pegarla en cualquier asistente de IA gratuito (ChatGPT, Claude,
Gemini…). Esos asistentes no conocen esta documentación por sí solos: dales el texto completo con
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (pega el enlace o adjunta el archivo) y
pídeles que respondan solo con él.

Hay otra opción gratuita de Google, la Gem [Learning coach](https://gemini.google.com/gem/learning-coach) de Gemini:
arma planes de estudio y te hace preguntas, pero no conoce esta documentación a menos que le pases `llms-full.txt`.
Su disponibilidad depende de tu cuenta y país.

## Qué aprenderás en cada fase

Cada fase de la [guía](implementacion/index.md) tiene un bloque **Aprende esta fase** con una analogía, los
conceptos clave, un reto práctico seguro y tres preguntas para comprobar lo aprendido.

| Fase | Idea central | Reto práctico |
|---|---|---|
| [0 — Preparación](implementacion/fase-0-preparacion.md) | Ansible automatiza tareas iguales en todos los equipos | Comprobar que Ansible llega a los nodos |
| [1 — Red](implementacion/fase-1-red.md) | Por qué los servidores necesitan IP fija y un bridge | Leer IP, máscara y gateway de un nodo |
| [2 — Incus](implementacion/fase-2-incus.md) | Contenedores, máquinas virtuales y quórum | Ver los miembros del clúster y sus instancias |
| [3 — K3s](implementacion/fase-3-k3s.md) | Kubernetes mantiene viva tu aplicación | Borrar un pod y ver cómo se repone |
| [4 — GitOps](implementacion/fase-4-gitops.md) | Git manda: Argo CD corrige cualquier diferencia | Comparar el clúster con lo que declara Git |
| [5 — vCluster](implementacion/fase-5-vcluster.md) | Clústeres virtuales dentro de un clúster | Explicar el inicio de sesión con GitHub en 4 pasos |
| [6 — CAPN](implementacion/fase-6-capn.md) | Clústeres creados a partir de un manifiesto | Generar el YAML de un clúster sin aplicarlo |

## Plantillas de pregunta

Si prefieres escribirla tú, estas sirven con cualquier asistente. Cambia lo que está entre corchetes.

```text
Actúa como mi tutor de estudio. Sigo la documentación de un HomeLab (Incus, K3s y GitOps con Argo CD).
Soy [principiante / intermedio / experto]. Quiero entender [concepto o paso]. Empieza por los conceptos
previos con una analogía, avanza de a poco y hazme una pregunta para comprobar que lo entendí antes de seguir.
```

```text
Hazme un cuestionario de 5 preguntas sobre [fase o sección], de a una, esperando mi respuesta.
Corrige cada respuesta y explica por qué.
```

```text
Algo me falló en [paso]. Ejecuté [comando] y vi [salida]. Hazme preguntas para diagnosticarlo y
guíame con las secciones de fallos de la documentación.
```

## Para estudiar mejor

- **Explica con tus palabras** lo que acabas de leer y pide que te corrija: es lo que más se aprende.
- **Haz el reto** de cada fase antes de pasar a la siguiente.
- **Pregunta el «por qué»**, no solo el «cómo»: la guía incluye el análisis de trade-offs de cada decisión.
- Si una respuesta de la IA no coincide con la documentación, **manda la documentación**.

!!! warning "Uso seguro"
    No pegues en ningún chat contraseñas, tokens, llaves privadas ni direcciones reales de tu red. Para pedir ayuda
    con un error, pega solo la salida del comando. La IA puede equivocarse: contrasta lo importante con la guía.

## Para quien enseña

El cuaderno sirve para trabajar en clase: cada estudiante usa su propia cuenta y su propio límite diario. Los bloques
**Aprende esta fase** se pueden usar como ejercicios guiados, y el [glosario](glosario.md) como apoyo. Si quieres
armar tu propio cuaderno o tutor, usa el texto completo de la guía en
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (el resumen está en
[`llms.txt`](https://homelab.maceo.cl/llms.txt)).
