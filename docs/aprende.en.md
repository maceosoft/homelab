# Learn with AI (free)

This HomeLab is designed so you learn while you build it. Next to each step of the guide there is a
**Learn with AI** button that prepares a tutor question with the context of that section and takes you to a study
notebook that **answers only from this documentation**. Everything used here is free.

## How to use it, in three steps

1. **Choose your level** in the bar that appears under the title of each guide page: *I'm just starting*,
   *Intermediate* or *Expert*. It changes how the artificial intelligence (AI) explains things: from everyday analogies
   to technical decisions.
2. **Click "Learn with AI"** next to the title of the step you're on and choose: **Explain it to me**, **Quiz me**
   or **Something went wrong**. The site copies the question and opens the notebook in another tab.
3. **Paste the question** into the notebook chat (`Ctrl+V`, or `⌘+V` on Mac) and start the conversation.

!!! note "Why do you have to paste?"
    NotebookLM doesn't allow opening a notebook with the question already filled in from a link. That's why the button copies the
    text and you paste it: one extra step, but it always works.

## The study notebook (NotebookLM)

[**Open the HomeLab notebook**](https://notebooklm.google/){ .md-button data-notebook-link="1" }

It's a [NotebookLM](https://notebooklm.google/) notebook with all of this documentation as its source. It answers only from
it and cites where each answer comes from, so it's unlikely to make things up. Besides chatting, you can ask it for:

- a **study guide** for a phase;
- a **quiz** or **flashcards** with an explanation for each answer;
- an **audio summary** to listen to while you do something else;
- a **mind map** of how the pieces connect.

**What you should know (free plan):**

- You need a **Google account**.
- Each account has a daily limit on chat questions and audio summaries (check the current limit in NotebookLM).
- The notebook is maintained by the project team; if the guide changed recently, it may take a while to catch up.

## If you don't want to use NotebookLM

The button always **copies the question**, so you can paste it into any free AI assistant (ChatGPT, Claude,
Gemini…). Those assistants don't know this documentation on their own: give them the full text with
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (paste the link or attach the file) and
ask them to answer only from it.

There is another free Google option, the Gemini Gem [Learning coach](https://gemini.google.com/gem/learning-coach):
it builds study plans and quizzes you, but it doesn't know this documentation unless you give it `llms-full.txt`.
Its availability depends on your account and country.

If you have access to the HomeLab (team `devops`), its own local assistant works too: in Open WebUI you can upload
`llms-full.txt` as a knowledge collection and ask questions against it (RAG, *Retrieval-Augmented Generation*). It runs on
the household's own machines, at no cost and without sending anything outside; it is slower than cloud assistants. See
[Local AI assistant](operacion/ia-ollama.md#ask-the-assistant-about-the-homelab-rag).

## What you'll learn in each phase

Each phase of the [guide](implementacion/index.md) has a **Learn this phase** block with an analogy, the
key concepts, a safe hands-on challenge and three questions to check what you've learned.

| Phase | Core idea | Hands-on challenge |
|---|---|---|
| [0 — Preparation](implementacion/fase-0-preparacion.md) | Ansible automates identical tasks across all machines | Check that Ansible reaches the nodes |
| [1 — Network](implementacion/fase-1-red.md) | Why servers need a static IP and a bridge | Read the IP, mask and gateway of a node |
| [2 — Incus](implementacion/fase-2-incus.md) | Containers, virtual machines and quorum | View the cluster members and their instances |
| [3 — K3s](implementacion/fase-3-k3s.md) | Kubernetes keeps your application alive | Delete a pod and watch it get replaced |
| [4 — GitOps](implementacion/fase-4-gitops.md) | Git is the source of truth: Argo CD corrects any difference | Compare the cluster with what Git declares |
| [5 — vCluster](implementacion/fase-5-vcluster.md) | Virtual clusters inside a cluster | Create a vCluster and log in with `vcluster connect` |
| [6 — CAPN](implementacion/fase-6-capn.md) | Clusters created from a manifest | Generate a cluster's YAML without applying it |

## Question templates

If you prefer to write it yourself, these work with any assistant. Replace what's between brackets.

```text
Actúa como mi tutor de estudio. Sigo la documentación de un HomeLab (Incus, K3s y GitOps con Argo CD).
Soy [principiante / intermedio / experto]. Quiero entender [concepto o paso]. Empieza por los conceptos
previos con una analogía, avanza poco a poco y hazme una pregunta para comprobar que lo entendí antes de seguir.
```

```text
Hazme un cuestionario de 5 preguntas sobre [fase o sección], una a una, esperando mi respuesta.
Corrige cada respuesta y explica por qué.
```

```text
Algo me falló en [paso]. Ejecuté [comando] y vi [salida]. Hazme preguntas para diagnosticarlo y
guíame con las secciones de fallos de la documentación.
```

## To study better

- **Explain in your own words** what you just read and ask to be corrected: it's how you learn the most.
- **Do the challenge** of each phase before moving on to the next.
- **Ask "why"**, not just "how": the guide includes the trade-off analysis for each decision.
- If an AI answer doesn't match the documentation, **the documentation wins**.

!!! warning "Safe use"
    Don't paste passwords, tokens, private keys or real addresses of your network into any chat. To ask for help
    with an error, paste only the command output. AI can be wrong: verify the important things against the guide.

## For teachers

The notebook works well for class: each student uses their own account and their own daily limit. The
**Learn this phase** blocks can be used as guided exercises, and the [glossary](glosario.md) as support. If you want to
build your own notebook or tutor, use the full text of the guide in
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (the summary is in
[`llms.txt`](https://homelab.maceo.cl/llms.txt)).
