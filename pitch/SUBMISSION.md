# Sorty: text for the MLH / OrganizerHQ submission

**Deadline: 6:00 PM sharp.** The guide says: "All projects are submitted on MLH (OrganizerHQ). Every team that presents has to submit." "Open the HackJam event page and click Challenges, then Submit a Project." "Don't forget to include frameworks and AI usage on it." "One submission per team. You can only win challenges you select!"

The guide does not list the form's field names, so the headings below are the usual ones. Paste each block into the field that matches. Everything here was checked against the code and the test logs at 5:00 PM today. The test counts come from single runs on computer-made pictures, and the text says so.

## For the team to decide or fill in first

- [ ] **Team name and members.** Marked `[team name]` and `[names]` below.
- [x] **Repository visibility.** The repo is public (made public at about 3:50 PM on the team's decision), so judges and organizers can open it and read the README. It shows the code, the renders, and the `pitch/` and `business/` folders.
- [ ] **Challenges.** Three are suggested below. You can only win what you select.
- [ ] **AI usage statement.** It matches the README's Credits section as of 5:00 PM. If you edit one, edit the other.
- [ ] **Demo link or video**, if the form asks. Sorty runs on your laptop, so there is no public address. Say "runs locally" or record a short screen video of the showcase.
- [ ] **Picture**, if the form asks: `sorty/design/renders/01_hero.png`.
- [ ] **"What we learned"**, if the form asks. That one has to be in your own words.

---

## Project name

```
Sorty
```

## One-line tagline

```
An AI camera, screen and voice for any bin: an instant alert for the items that wreck a whole load of recycling, and the right bin for everything else.
```

## Description

```
Sorty is an AI assistant for waste stations. A camera on the bin sees what a person is holding, and a screen and a voice tell them which bin to use.

A few items wreck recycling for everyone. Batteries, vapes and phones can start fires: Hillsborough County, in a warning about lithium batteries, reports over 30 garbage and recycling truck fires in three years. Plastic bags jam the sorting machines: the City of Tampa says tangling items stop its sorting line for up to three hours a day. Food and liquid spoil the paper around them.

So Sorty runs two AI models at the same moment. A small fast one only asks: will this wreck the load? If it is sure, the screen turns red and Sorty says "Stop!" in about a second, with where the item goes instead. The careful one knows what it cannot see. When the answer is visible, it answers at once. When another view would show it, it asks you to open or turn the item. For a small detail, it looks closer. When no camera can know, it asks one short question. Then it names the bin, lights it up and gives a short reason.

Today Sorty is a virtual prototype: real software on live AI models, and a bin station designed in Blender and shown in an animated web page. No hardware has been built.
```

## How we built it

```
We built Sorty today, during HackJam '26.

The brain is a Python program with two parts that start at the same moment on the same camera picture. The instant alert sends a small picture to the fastest Claude model (Claude Haiku 5.5) with one question: is this one of the few things that wreck a whole load? The careful part sends the picture and the station's bin rules to Claude Opus 5.5, which must pick one of four moves: answer, ask for another view, take a second, closer look at a zoomed copy of the picture, or ask the person a question. The careful part is orchestrated as a LangGraph graph (think, closer check, person, with a pause while the person answers); a plain loop does the same job as a fallback. Some limits are enforced in code: at most three requests to the person per item, only bins that exist on the station can be named, a spending cap, and a fallback message ("Please check the labels on the bins") when the AI cannot be reached.

A small local web server links the brain to the screen page, which is plain HTML, CSS and JavaScript and uses the browser's own speech and camera features. The same page runs inside our virtual prototype.

The bin station, the layers of the animated prototype and our 31 test pictures are Blender renders made by Python scripts.

We directed an AI coding assistant, Claude Code, which wrote the code (see "AI usage").

Testing: 157 and 56 automatic checks of the code pass; they test the plumbing, not the AI's judgement. With the live AI today, in single runs on computer-made pictures: a one-look version of the same AI got 28 of our 33 written test cases right, and Sorty got 32 of 33. On the LangGraph orchestrator Sorty got 35 of 36. The instant alert caught 10 of 10 showings of load-wrecking items, with no false alarm in 52 showings of ordinary items, in about one second each. The one miss was a paper coffee cup. Nothing has been tested with a real bin camera, real hardware or a real person using it. Support for Google's Gemini is written but has not been run.
```

## Frameworks and tools

Copied from the README's Credits section.

```
Brain and server: Python 3.13; the official Anthropic Python SDK (anthropic) to call the Claude API; LangGraph with langchain-anthropic and langchain-google-genai for the graph form of the decision loop; Pillow for image handling; Python's standard library web server (no web framework).

AI models inside the product: Claude with vision, by Anthropic. claude-opus-5-5 decides which bin an item goes in (the Faster mode uses claude-sonnet-5-5), and claude-haiku-5-5 is the instant alert. Google's Gemini (gemini-3.8-flash) is supported in code through LangGraph but has not been run yet.

Screen, voice and virtual prototype: plain HTML, CSS and JavaScript with no framework and no build step; the browser's Web Speech API (speech synthesis and recognition), Web Audio API and camera API (getUserMedia).

3D design, renders and test pictures: Blender 5.2 (Cycles renderer), driven by Python scripts; FFmpeg to stitch images and encode the turntable video; system fonts.

Development: Claude Code (Anthropic's AI coding assistant, running Claude Fable 5.2), Git and GitHub.
```

If the form wants short tags instead:

```
Python, Anthropic Claude API, Anthropic Python SDK, LangGraph, LangChain, Pillow, HTML, CSS, JavaScript, Web Speech API, Web Audio API, Blender, FFmpeg, Claude Code, Git, GitHub
```

## AI usage

```
We used AI in two ways, and we want to be plain about both.

Inside the product: the sorting decisions are made by Anthropic's Claude vision models at run time: Claude Opus 5.5 for the careful answer and Claude Haiku 5.5 for the instant alert. Without an API key, Sorty runs in a clearly labelled practice mode with scripted answers.

To build the project: all source code in the repository was written by Claude Code, Anthropic's AI coding assistant, working from our instructions. That covers the brain, the server, the screen and voice, the virtual prototype, the pitch deck and the tests. Claude Code also wrote the Blender scripts. Every image and video in the repository is a Blender render produced by those scripts; we used no AI image generator, no stock photos and no downloaded 3D models. Claude Code also drafted the written documents: the README, the pitch script, the cost estimate, the bin rules and the 36 test scenarios, and it looked up the outside figures we quote (the sources are listed in pitch/WRECKER_FACTS.md). The research summarised in the README's design table was recalled by the AI from published work and has not been checked against the original papers by the team.

What the team did: we chose the problem and came up with the idea, a camera assistant that can be added to any bin. We defined how it must behave: speak and show the answer, raise an instant alert for items that wreck a whole load, ask the person to open or turn an item and look again, run a vision check for small details, and ask a question when no camera can know. We made the product decisions: three bins, a design built around how people behave, which AI service to use, two models running side by side, testing against many scenarios, a Blender design, and a virtual prototype instead of a physical one. We directed and reviewed the AI's work throughout, and prepared and gave the pitch.

The README has the full list in its "Credits: tools, frameworks and AI usage" section.
```

## Challenges to select

| Select | Why it fits (one sentence) |
|---|---|
| **Off the Grid** | Sorty goes after the items that wreck recycling, by changing what people do at the bin, one item at a time, and it is made to fit bins that already exist. |
| **Home Turf** | It starts from local problems: Hillsborough County's garbage and recycling truck fires and the City of Tampa's sorting line stopped by tangling items; its bin rules are one settings file that can be set to match the bins on our campus. |
| **Best Overall** | One idea is carried all the way through: two working AI models side by side, a screen and voice designed for how people behave, a station design, an animated virtual prototype, tests with counts, and a cost estimate. |

Do not select the **Gemini API** challenge unless a Gemini key has been added and the Gemini path has been run. Today Sorty runs on Claude; the Gemini support is written but untested.

If the form has one text box for "why this challenge":

```
Off the Grid: Sorty goes after the items that wreck recycling, by changing what people do at the bin, one item at a time, and it is made to fit bins that already exist.

Home Turf: it starts from local problems: Hillsborough County's garbage and recycling truck fires and the City of Tampa's sorting line stopped by tangling items. Its bin rules are one settings file that can be set to match the bins on our campus.

Best Overall: one idea carried all the way through: two working AI models side by side, a screen and voice designed for how people behave, a station design, an animated virtual prototype, tests with counts, and a cost estimate.
```

## Repository link

```
https://github.com/alexanderdemarco746-lab/r-xgnbn5ji39
```

**This repository is public.** Anyone with the link can read it, including the README's Credits section that the guide's AI-credit rule is written around. The AI usage text above is in the form as well.

## Team

```
[team name]
[names of up to three members]
```

---

## Extra blocks, only if the form asks for them

### What's next

```
Test with a real camera and real trash, with real people. Put the instant alert on the bin's own computer with a small trained detector, so it works without the internet. Match the rules file to Tampa's own program. Make the careful answer faster: today it needs about 3 seconds for an obvious item and 5 to 12 for a hidden one. Build one kit; our parts list comes to about 340 dollars on paper.
```

### Challenges we ran into

```
We had no time to build hardware, so we built a virtual prototype around the real software. The careful AI is slower than a person at a bin wants to wait, which is why the dangerous items got their own one-second alert. And we had to decide when Sorty should ask a question and when a short warning is enough.
```

### Sources for the numbers above

```
Truck fires: Hillsborough County news release "Lithium-Ion Batteries Pose a Fire Risk When Disposed in the Garbage or Recycling", December 9, 2025.
Sorting line stopped up to three hours a day: City of Tampa recycling FAQ.
Test counts: sorty/tests/results in the repository (REPORT.md, REPORT_lg_full.md, GUARD.md), run on November 21, 2026.
Parts estimate: seller prices checked November 21, 2026 (business/COST_ESTIMATE.md in the repository).
All outside figures with their links: pitch/WRECKER_FACTS.md in the repository.
```
