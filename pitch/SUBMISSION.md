# Sorty: text for the MLH / OrganizerHQ submission

**Deadline: 6:00 PM sharp.** The guide says: "All projects are submitted on MLH (OrganizerHQ). Every team that presents has to submit." "Open the HackJam event page and click Challenges, then Submit a Project." "Don't forget to include frameworks and AI usage on it." "One submission per team. You can only win challenges you select!"

The guide does not list the form's field names, so the headings below are the usual ones. Paste each block into the field that matches. Everything here was true at 3:15 PM today; nothing claims an accuracy figure.

## For the team to decide or fill in first

- [ ] **Team name and members.** Marked `[team name]` and `[names]` below.
- [x] **Repository visibility.** The repo is public (made public at about 3:50 PM on the team's decision), so judges and organizers can open it and read the README. It shows the code, the renders, and the `pitch/` and `business/` folders.
- [ ] **Challenges.** Three are suggested below. You can only win what you select.
- [ ] **AI usage statement.** It matches the README's Credits section as of 3:15 PM. If you edit one, edit the other.
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
The bin that knows what it cannot see: an AI camera, screen and voice that tell you which bin your trash goes in.
```

## Description

```
Sorty is an AI assistant for waste stations. A camera on the bin sees what a person is holding, and a screen and a voice tell them which bin to use.

In 2020 the City of Tampa reported that 36% of what residents put in recycling was not recyclable. Signs cannot fix that when the answer is hidden: is the pizza box greasy inside, is the can empty?

Sorty knows what it cannot see. When the answer is visible, it answers at once. When another view would show it, it asks you to open or turn the item. For a small detail, it looks closer. When no camera can know, it asks one short question. Then it names the bin, lights it up and gives a short reason.

Today Sorty is a virtual prototype: real software on a live AI model, and a bin station designed in Blender and shown in an animated web page. No hardware has been built.
```

## How we built it

```
We built Sorty today, during HackJam '26.

The brain is a Python program. It sends the camera picture and the station's bin rules to Anthropic's Claude vision model, which must pick one of four moves: answer, ask for another view, run a closer check on the picture, or ask the person a question. The limits are enforced in code: at most three requests to the person, only bins that exist on the station, and always an answer.

A small local web server links the brain to the screen page, which is plain HTML, CSS and JavaScript and uses the browser's own speech and camera features. The same page runs inside our virtual prototype.

The bin station, the layers of the animated prototype and our 27 test pictures are Blender renders made by Python scripts.

We directed an AI coding assistant, Claude Code, which wrote the code (see "AI usage").

Testing: 107 automatic checks of the code pass. 32 test cases are prepared. Two items were run on the live AI today, a half-full soda can and a greasy pizza box, and both were sorted correctly. That is two items, not an accuracy figure. Nothing has been tested with a real bin camera or real hardware.
```

## Frameworks and tools

Copied from the README's Credits section.

```
Brain and server: Python 3.13; the official Anthropic Python SDK (anthropic) to call the Claude API; Pillow for image handling; Python's standard library web server (no web framework).

AI model inside the product: Claude with vision (claude-opus-5-5 by default), by Anthropic. It decides which bin an item goes in.

Screen, voice and virtual prototype: plain HTML, CSS and JavaScript with no framework and no build step; the browser's Web Speech API (speech synthesis and recognition), Web Audio API and camera API (getUserMedia).

3D design, renders and test pictures: Blender 5.2 (Cycles renderer), driven by Python scripts; FFmpeg to stitch images and encode the turntable video; system fonts.

Development: Claude Code (Anthropic's AI coding assistant, running Claude Fable 5.2), Git and GitHub.
```

If the form wants short tags instead:

```
Python, Anthropic Claude API, Anthropic Python SDK, Pillow, HTML, CSS, JavaScript, Web Speech API, Web Audio API, Blender, FFmpeg, Claude Code, Git, GitHub
```

## AI usage

```
We used AI in two ways, and we want to be plain about both.

Inside the product: the sorting decisions are made by Anthropic's Claude vision model at run time. Without an API key, Sorty runs in a clearly labelled practice mode with scripted answers.

To build the project: all source code in the repository was written by Claude Code, Anthropic's AI coding assistant, working from our instructions. That covers the brain, the server, the screen and voice, the virtual prototype and the tests. Claude Code also wrote the Blender scripts. Every image and video in the repository is a Blender render produced by those scripts; we used no AI image generator, no stock photos and no downloaded 3D models. Claude Code also drafted the written documents: the README, the pitch script, the cost estimate, the bin rules and the 32 test scenarios. The research summarised in the README's design table was recalled by the AI from published work and has not been checked against the original papers by the team.

What the team did: we chose the problem and came up with the idea, a camera assistant that can be added to any bin. We defined how it must behave: speak and show the answer, ask the person to open or turn an item and look again, run a vision check for small details, and ask a question when no camera can know. We made the product decisions: three bins, a design built around how people behave, which AI service to use, testing against many scenarios, a Blender design, and a virtual prototype instead of a physical one. We directed and reviewed the AI's work throughout, and prepared and gave the pitch.

The README has the full list in its "Credits: tools, frameworks and AI usage" section.
```

## Challenges to select

| Select | Why it fits (one sentence) |
|---|---|
| **Off the Grid** | Sorty goes after recycling contamination by changing what people do at the bin, one item at a time, and it is made to fit bins that already exist. |
| **Home Turf** | It starts from a local problem, the City of Tampa's own 2020 figure of 36% contamination in residential recycling, and its bin layout is one settings file that can be set to match the bins on our campus. |
| **Best Overall** | One idea is carried all the way through: a working AI brain, a screen and voice designed for how people behave, a station design, an animated virtual prototype, tests and a cost estimate. |

Do not select the **Gemini API** challenge. Sorty uses Claude, not Gemini.

If the form has one text box for "why this challenge":

```
Off the Grid: Sorty goes after recycling contamination by changing what people do at the bin, one item at a time, and it is made to fit bins that already exist.

Home Turf: it starts from a local problem, the City of Tampa's own 2020 figure of 36% contamination in residential recycling, and its bin layout is one settings file that can be set to match the bins on our campus.

Best Overall: one idea carried all the way through: a working AI brain, a screen and voice designed for how people behave, a station design, an animated virtual prototype, tests and a cost estimate.
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
Run our 32 test cases on the live AI and report the result, whatever it is. Test with a real camera and real trash. Make it faster: today the AI needs about 5 to 12 seconds per item. Build one kit; our parts list comes to about 340 dollars on paper.
```

### Challenges we ran into

```
We had no time to build hardware, so we built a virtual prototype around the real software. The AI is slower than a person at a bin wants to wait. And we had to decide when Sorty should ask a question and when a short warning is enough.
```

### Sources for the numbers above

```
36% contamination: City of Tampa news release "City of Tampa Announces New Recycling Contract", posted August 3, 2020.
Parts estimate: seller prices checked November 21, 2026 (business/COST_ESTIMATE.md in the repository).
```
