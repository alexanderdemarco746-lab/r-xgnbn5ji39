# Text for the MLH "Project Details" form

The form has three required fields: Project name, Source code, Description (Markdown). The guide asks for frameworks and AI usage to be included, so they are inside the description.

## Project name

```
Sorty
```

## Source code

```
https://github.com/alexanderdemarco746-lab/r-xgnbn5ji39
```

## Description

Everything between the two marker lines below goes into the Description box, as it is (it is Markdown).

<!-- DESCRIPTION START -->
**Sorty: an AI camera, screen and voice for any bin.** An instant alert for the items that wreck a whole load of recycling, and the right bin for everything else.

## The problem

A few items wreck recycling for everyone. Batteries, vapes and phones can start fires: Hillsborough County, in a warning about lithium batteries, reports over 30 garbage and recycling truck fires in three years. Plastic bags jam the sorting machines: the City of Tampa says tangling items stop its sorting line for up to three hours a day. Food and liquid spoil the paper around them. On top of that, people guess wrong on everyday items, and signs alone do not fix it.

## What Sorty does

A camera on the bin sees what a person is holding, and a screen and a voice tell them which bin to use. Behind it is a multi-agent workflow that starts on one camera picture:

1. **Alert agent** (a small, fast vision model): will this wreck the load? If it is sure, the screen turns red and Sorty says "Stop!" in about a second, with where the item goes instead.
2. **Orchestrator agent** (Claude Opus 5.5, run as a LangGraph graph): finds the fact that decides the bin, then picks one move: answer, ask to see another side, call a closer check, or ask one short question.
3. **Inspector agent**: a closer look at a zoomed picture for grease, food or mold.
4. **Label agent**: reads recycling codes and compostable marks.

Then Sorty names the bin, lights it up and gives one short reason, in English or Spanish. It makes at most three requests per item and always ends with an answer.

Today Sorty is a virtual prototype: real software on live AI models, and a bin station designed in Blender and shown in an animated web page. No hardware has been built.

## Tested today

Single runs on computer-made pictures, with the live AI:

- Instant alert: caught 10 of 10 showings of load-wrecking items, with no false alarm in 52 showings of ordinary items, in about one second each.
- 33 written test cases: a one-look version of the same AI got 28 right, Sorty got 32.
- On the LangGraph orchestrator: 35 of 36 right.
- 169 and 56 automatic checks of the code pass.

Not tested: a real bin camera, real hardware, real people using it. Support for Google's Gemini and for TypeSafe AI's Jev is written but has not been run against the real services.

## How we built it

We built Sorty today, during HackJam '26. The brain is a Python program. The alert agent and the orchestrator start at the same moment on the same camera picture; the orchestrator calls the inspector and label agents only when it needs them. Limits are enforced in code: at most three requests to the person per item, only bins that exist on the station can be named, a spending cap, and a fallback message ("Please check the labels on the bins") when the AI cannot be reached. A small local web server links the brain to the screen page, which uses the browser's own speech and camera features. The bin station, the animated prototype's layers and our 31 test pictures are Blender renders made by Python scripts.

## Frameworks and tools

- **Brain and server:** Python 3.13; the official Anthropic Python SDK to call the Claude API; LangGraph with langchain-anthropic and langchain-google-genai for the orchestrator graph; Pillow; Python's standard library web server.
- **AI models inside the product:** Anthropic's Claude with vision: Claude Opus 5.5 (orchestrator, inspector and label agents; Claude Sonnet 5.5 in the Faster mode) and Claude Haiku 5.5 (alert agent). Google's Gemini and TypeSafe AI's Jev are supported in code but not yet run.
- **Screen, voice, virtual prototype and pitch deck:** plain HTML, CSS and JavaScript with no framework; the browser's Web Speech API, Web Audio API and camera API.
- **3D design, renders and test pictures:** Blender 5.2 driven by Python scripts; FFmpeg.
- **Development:** Claude Code (Anthropic's AI coding assistant, running Claude Fable 5.2), Git and GitHub.

## AI usage

We used AI in two ways, and we want to be plain about both.

**Inside the product:** the sorting decisions and the instant alert are made by Anthropic's Claude vision models at run time. Without an API key, Sorty runs in a clearly labelled practice mode with scripted answers.

**To build the project:** all source code in the repository was written by Claude Code, Anthropic's AI coding assistant, working from our instructions: the brain, the server, the screen and voice, the virtual prototype, the pitch deck and the tests. Claude Code also wrote the Blender scripts; every image and video in the repository is a Blender render produced by those scripts (no AI image generator, no stock photos, no downloaded 3D models). Claude Code also drafted the written documents (README, pitch script, cost estimate, bin rules, test scenarios) and looked up the outside figures we quote.

**What the team did:** we chose the problem and came up with the idea; defined how Sorty must behave (the instant alert for items that wreck a load, looking again, asking when no camera can know); made the product decisions; and directed and reviewed the AI's work throughout, and prepared and gave the pitch.

The README's "Credits: tools, frameworks and AI usage" section has the full list.

## Sources

- Truck fires: Hillsborough County news release, "Lithium-Ion Batteries Pose a Fire Risk When Disposed in the Garbage or Recycling", December 9, 2025.
- Sorting line stopped up to three hours a day: City of Tampa recycling FAQ.
- Our test counts: `sorty/tests/results` in the repository, run on November 21, 2026.
- All outside figures with links: `pitch/WRECKER_FACTS.md` in the repository.
<!-- DESCRIPTION END -->
