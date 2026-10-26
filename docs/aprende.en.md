# Learn with AI (free)

This HomeLab is designed for you to learn as you build it. Alongside each step of the guide, there is a **Learn with AI**
button that prepares a tutor question with the context of that section and takes you to a study notebook that **only
responds with this documentation**. Everything used here is free.

## How to use it, in three steps

1. **Choose your level** in the bar that appears under the title of each guide page: *I'm starting*, *Intermediate*, or
   *Expert*. Change how the artificial intelligence (AI) explains things: from everyday analogies to technical
   decisions.
2. **Press «Learn with AI»** next to the title of the step you are on and choose: **Explain it to me**, **Quiz me**, or
   **Something went wrong**. The site copies the question and opens the notebook in another tab.
3. **Paste the question** in the chat of the notebook (`Ctrl+V`, or `⌘+V` on Mac) and converse.

!!! note "Why paste?"
    NotebookLM does not allow opening a notebook with the question already written from a link. That's why the button
    copies the text and you paste it: an extra step, but it always works.

## The study notebook (NotebookLM)

[**Open the HomeLab notebook**](https://notebooklm.google/){ .md-button data-notebook-link="1" }

It is a notebook of [NotebookLM](https://notebooklm.google/) with all this documentation as the source. It responds only
with it and cites where each answer comes from, so it's hard for it to make things up. Besides chatting, you can ask it
for:

- a **study guide** for a phase;
- a **quiz** or **flashcards** with an explanation of each answer;
- an **audio summary** to listen to while doing something else;
- a **mind map** of how the pieces connect.

**What to know (free plan):**

- You need a **Google account**.
- Each account has a daily limit of chat questions and audio summaries (check the current limit in NotebookLM).
- The notebook is maintained by the project team; if the guide has changed recently, it may take time to update.

## If you don't want to use NotebookLM

The button always **copies the question**, so you can paste it into any free AI assistant (ChatGPT, Claude, Gemini…).
These assistants do not know this documentation on their own: give them the full text with
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (paste the link or attach the file) and ask them to respond
only with it.

There is another free option from Google, the Gem [Learning coach](https://gemini.google.com/gem/learning-coach) of
Gemini: it creates study plans and quizzes you, but it does not know this documentation unless you pass it
`llms-full.txt`. Its availability depends on your account and country.

If you have access to the HomeLab (team `devops`), its own local assistant also works: in Open WebUI you can upload
`llms-full.txt` as a knowledge collection and ask it with it (RAG, *Retrieval-Augmented Generation*). It runs on home
machines, at no cost and without sending anything outside; it is slower than cloud assistants. See
[Local AI Assistant](operacion/ia-ollama.md#ask-the-assistant-about-the-homelab-rag).

## What you will learn in each phase

Each phase of the [guide](implementacion/index.md) has a **Learn this phase** block with an analogy, key concepts, a
safe practical challenge, and three questions to check what you've learned.

| Phase | Central idea | Practical challenge |
|---|---|---|
| [0 — Preparation](implementacion/fase-0-preparacion.md) | Ansible automates identical tasks on all machines | Check that Ansible reaches the nodes |
| [1 — Network](implementacion/fase-1-red.md) | Why servers need a fixed IP and a bridge | Read IP, mask, and gateway of a node |
| [2 — Incus](implementacion/fase-2-incus.md) | Containers, virtual machines, and quorum | See the cluster members and their instances |
| [3 — K3s](implementacion/fase-3-k3s.md) | Kubernetes keeps your application alive | Delete a pod and see how it recovers |
| [4 — GitOps](implementacion/fase-4-gitops.md) | Git dictates: Argo CD corrects any difference | Compare the cluster with what Git declares |
| [5 — vCluster](implementacion/fase-5-vcluster.md) | Virtual clusters inside a cluster | Explain the login with GitHub in 4 steps |
| [6 — CAPN](implementacion/fase-6-capn.md) | Clusters created from a manifest | Generate the YAML of a cluster without applying it |

## Question templates

If you prefer to write it yourself, these work with any assistant. Change what is between brackets.

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

- **Explain in your own words** what you just read and ask for corrections: this is what you learn the most.
- **Do the challenge** of each phase before moving on to the next.
- **Ask the «why»**, not just the «how»: the guide includes the analysis of trade-offs for each decision.
- If an AI response does not match the documentation, **send the documentation**.

!!! warning "Safe use"
    Do not paste in any chat passwords, tokens, private keys, or real addresses of your network. To ask for help with an
    error, paste only the command output. The AI can be wrong: check the important parts with the guide.

## For those who teach

The notebook works for classroom use: each student uses their own account and daily limit. The **Learn this phase**
blocks can be used as guided exercises, and the [glossary](glosario.md) as support. If you want to create your own
notebook or tutor, use the full text of the guide in
[`llms-full.txt`](https://homelab.maceo.cl/llms-full.txt) (the summary is in
[`llms.txt`](https://homelab.maceo.cl/llms.txt)).
