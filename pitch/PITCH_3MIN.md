# Sorty: 3-minute pitch for HackJam '26

This is the team's speaking script and preparation sheet. It follows the official "HackJam '26 | Hacker's Guide"; quotes from the guide are word for word. Facts about Sorty were checked against the code and the test logs, and every outside statistic against its source, on November 21, 2026 (last pass 5:00 PM).

## Structure check

The pitch has to cover six parts. The deck has five slides, so each part is tied to the slide on screen.

| Part | In the earlier script? | Where the script below covers it | Slide |
|---|---|---|---|
| 1. What is the problem | Yes, but it led with ordinary confusion | Part 1: the few items that wreck a whole load, then everyday wrong guesses | 1 |
| 2. Why current solutions do not cover our main problem | Barely: one sentence about signs | Part 2: signs fall short, a one-look camera misses what is hidden, nothing we found looks again or asks | 2 |
| 3. The impact of the problem | One sentence | Part 3: the county's truck fires and Tampa's stopped sorting line. Said right after Part 1, because problem and impact share slide 1 | 1 |
| 4. How our prototype solves it | Yes, but with no walk through the system | Part 4: what we build (a fast alert and a careful model), how it works, then the live demo | 3, 4, showcase |
| 5. The benefits of our product | Not as its own part | Part 5 | 5 |
| 6. The potential big benefits | Mixed into the close | Part 6, tied to a sourced trial | 5 |
| Honest close | Yes | Close: today's test counts, and what does not exist | 5 |

The guide's own elements are covered: introduce the project (Part 1, first sentence), explain the problem (Parts 1 to 3), describe the solution (Part 4), demonstrate the main features (live demo).

---

## The script

**About 380 spoken words.** About 284 of them are outside the demo: about 2 minutes 2 seconds at a calm 140 words a minute. The live demo (the fast tour, then one pizza box) takes about 55 seconds, and the speaker talks over the waiting. Total: about **2:58**, which leaves no slack: use the first cut below if you start late. At a slow pace it runs past 3:00, so rehearse once with a stopwatch and use the cuts under "If you are behind".

The 56 seconds is an estimate from today's measured AI times plus the animation. The page has not been timed with these three items.

Lines starting with `>` are spoken. Lines in [brackets] are what happens on screen.

### Slide 1 on screen: What's the problem

**Part 1. The problem**

> We are [team name], and this is Sorty, in the Off the Grid track. A few items wreck recycling for everyone: batteries start fires, plastic bags jam the sorting machines, and food or liquid spoils the paper around it. People also guess wrong on everyday items.

**Part 3. The impact** (said here: problem and impact share one slide)

> Hillsborough County reports over 30 truck fires in three years; Tampa says tangling items stop its sorting line up to three hours a day.

### Slide 2 on screen: Why current efforts fail

**Part 2. Why current solutions do not cover it**

> Signs alone fall short, and a camera that looks once misses what is hidden. We found no product that looks again or asks.

### Slide 3 on screen: What we build

**Part 4. How our prototype solves it**

> So we built Sorty: a camera, a screen and a voice for any bin, with two AI models. A small fast one only asks: will this wreck the load?

> Measured today on our pictures: 10 of 10 wreckers caught, no false alarm in 52 tries, about one second, against five for the careful model.

### Slide 4 on screen: How it works

> How it works: a multi-agent workflow. A sensor notices an item; the camera takes one picture, and two agents start at once: the alert agent and the orchestrator, a LangGraph graph. The orchestrator finds the deciding fact, then picks one of four moves: answer, ask to see another side, call an inspector agent for a closer look, or ask one question. Then one answer with a reason, and the right bin lights up.

### Showcase page on screen: live demo

[Press "Play fast tour". A line of eight people forms. The first is in a hurry and walks straight at the blue bin with batteries.]

> Live now: a line of people. The first is in a hurry and just throws batteries at the recycling.

[The scene turns red: "STOP", with the time it took. The line moves on: bottle, plastic bag (red again), banana peel, vape (red again), box, chip bag, glass bottle. The stopwatch on the stage counts. In today's one timed run: 8 people in 30.9 seconds.]

> The alert agent stopped him in about a second. Everyone else gets a bin in two or three seconds. An AI assistant wrote the code from our instructions.

[When the stopwatch stops, read its numbers out instead of these if they differ.]

> Eight people, about thirty seconds.

[Click "Pizza box, greasy inside". Sorty: "Open the box and show the inside." Let the judge hear it.]

> Now a closed pizza box. The orchestrator asks to look inside, then calls the inspector agent for a closer look.

[The box opens. A wait of 6 to 9 seconds. Sorty: "Green bin, in the middle." The green bin lights up. Stay quiet and let Sorty speak.]

> Grease inside: green bin. One picture could not have told.

### Slide 5 on screen: Potential benefits

**Part 5. The benefits, today**

> Today: one clear answer with a reason, in about a second for the dangerous items.

**Part 6. The potential big benefits** (the slide shows six, each with its source; say four)

> At scale: fewer fires, sorting lines that keep running, cleaner loads, lower costs. In one university trial, a trained helper at the bin cut wrong items by 85 percent or more.

**Close**

> Today's test, computer-made pictures: Sorty 32 of 33 written cases, one look 28. No real camera, no real people, no hardware yet. Thank you.

### If the red alert does not appear on the page

The fast alert was measured on its own at 4:46 PM, and at 4:50 PM it was checked through the running server and on Sorty's screen: a vape, a plastic bag and batteries each turned the screen red in 1 to 2 seconds. It is wired into the showcase page too. If the red screen still does not appear at pitch time, the careful model answers the batteries a few seconds later. In place of "The fast model caught it at once", say: "This time the careful model answered. The fast alert caught 10 of 10 in today's test."

### If you are behind

- **First cut:** leave out "People also guess wrong on everyday items."
- **At 2:15 on your clock**, go to slide 5 even if the pizza box has not finished.
- **If the fast tour took more than 40 seconds**, skip the pizza box and say: "A closed pizza box makes Sorty ask to look inside: greasy goes in the green bin, clean in the blue. It did in today's test."
- **If the tour will not start**, click the card "AA batteries" for the red alert, then "Pizza box, greasy inside".
- **If an item comes out wrong**, say so: "That one is wrong." Then carry on.

### If asked about the orchestrator

LangGraph is in the timed script ("run as a LangGraph graph"). If a judge asks how it is built:

> The careful model's steps are a LangGraph graph: think, run a closer check, or pause for the person and resume. On today's 36 written cases it got 35 right on Claude. It is built to run on Gemini too, not yet verified.

The 33-case comparison with the one-look camera (Sorty 32, one look 28) used the earlier plain loop; the LangGraph run came after it, on 36 cases, with the same single miss (the coffee cup's sleeve). LangGraph is now the default. Never say "works on Gemini": no Gemini call has been made.

---

## Before judging: nine things to get right

1. **README credits.** The guide says: "You must credit any tools used and be clear on what you made and what was generated by having a detailed readme... If you do not credit your AI usage, you will be disqualified". The README has a "Credits: tools, frameworks and AI usage" section. What is said at the table must agree with it.
2. **Submission closes at 6:00 PM sharp** on MLH (OrganizerHQ). The text is in `pitch/SUBMISSION.md`. "You can only win challenges you select!" Sorty fits **Off the Grid**, **Home Turf** and **Best Overall**.
3. **Say the tests as counts, never percentages**, and say what they are: cases the team wrote, on computer-made pictures of single items. Not real photos, not real people.
4. **The models are pretrained.** The team trained nothing. If asked about training data, the honest answer is that there is none of ours.
5. **Warm up before the judge arrives.** The first run after starting is slow. Play one pizza box shortly before the judge reaches the table.
6. **Know which mode the page is in.** The badge should read "Live AI: claude-opus-5-5". If it reads "Practice mode: scripted answers, no AI key", say once that the answers are scripted.
7. **Know what a dead network does.** Each item ends with "Please check the labels on the bins". For scripted answers use the Practice mode switch if the page has one; otherwise restart with `sorty\run.bat --mock`. Keep a phone hotspot ready.
8. **Mind the AI budget.** A guard stops AI use at 5 dollars; about $2.35 was used by 4:32 PM. One rehearsal of the three-item demo costs about 8 cents. When the limit is reached the page drops to practice mode by itself.
9. **Judging is 6:20 PM to 7:50 PM** at the team's table. Start `sorty\run.bat`, open `http://localhost:8787/showcase/` in Chrome or Edge, leave Faster mode unticked, Auto-answer ticked and Sound on, and press Esc so the scene is empty.

---

## What the guide asks for

"Each team will have approximately 5 minutes to present its project to the assigned judge."

| Guide, word for word | Where the script covers it |
|---|---|
| "3 minutes – Project Showcase: Introduce your project, | Part 1, first sentence |
| explain the problem it addresses, | Parts 1, 3 and 2 (slides 1 and 2) |
| describe your solution, | Part 4 (slides 3 and 4) |
| and demonstrate its main features." | Live demo of three items on the showcase page |
| "1 minute – Judge Questions: Answer questions about your project's functionality, technical implementation, and design decisions." | "Likely questions" below, sorted into those three kinds |
| "1 minute – Transition" | Nothing to say. Stop talking at 3:00 |

"Projects will be evaluated across five categories, each with a different weight contributing to the final score." "Each criterion is scored on a scale of 1 to 5, with 5 representing the highest score."

| Criterion and weight (word for word) | The lines that earn it | Proof on screen | What is not done |
|---|---|---|---|
| "Technical Implementation — 25%" | Slide 3: "two AI models"; "10 of 10 wreckers caught, no false alarm in 52 tries". Slide 4: "both models start at once"; "picks one of four moves". Demo: "The careful model, Claude Opus 5.5"; "the code holds the limits". Close: "Sorty 32 of 33 written cases, one look 28" | The red alert screen, "How Sorty decided" and "What the camera sees" during the demo; `sorty/tests/results/REPORT.md` and `GUARD.md` if asked | Both tests are the team's own, on computer-made pictures. The alert was measured on five wrecker pictures. No real photo, no real bin |
| "Innovation & Creativity — 20%" | Slide 2: "We found no product that looks again or asks". Slide 3: a fast alert beside a careful model. Demo: "One picture could not tell these two apart" | The red "Stop" screen; the same closed box going to two different bins | "We found no product" is not proof that none exists |
| "Relevance to the Track — 20%" | Slide 1: "in the Off the Grid track"; "A few items wreck recycling for everyone"; the county's truck fires and Tampa's stopped sorting line. Slide 5: the helper at the bin | The alert on batteries; the lit bin and Sorty's spoken reason | No change in what people do has been measured. The local figures are the county's trucks and the city's plant, not a campus bin. The demo station is a sample, not Tampa's rules |
| "Execution & Completeness — 20%" | Three full live runs in the demo. Close: the test counts, and "No real camera, no real people, no hardware yet" | The showcase running end to end on the live AI, with the real screen software on the right | No physical bin, no camera on a bin, nobody has used it |
| "Presentation & Understanding — 15%" | Five slides, six parts, plain words; the honest close | One speaker at a time, calm pace | Every teammate must be able to give the "know this by heart" answer without notes |

Main track, **Off the Grid**: "All about sustainability. Work on a project that emphasizes sustainable development. Saving water, reusable and clean energy, green transportation, or changing people's action."

| "What we look for" (word for word) | Where the script covers it |
|---|---|
| "A sustainable approach to a problem" | Part 6: a helper on bins a site already has |
| "Tackling a problem that threatens the environment or influences it negatively" | Parts 1 and 3: the items that wreck a load |
| "A project that advocates sustainable development" | Part 5: one clear answer with a reason |

Also selected, if checked on MLH: **Home Turf** (Part 3 uses Hillsborough County's and the City of Tampa's own figures) and **Best Overall**.

---

## Evidence and sources

### In the spoken script

| Spoken claim | Source and year | Fine print |
|---|---|---|
| Batteries start fires | US EPA, "Used Lithium-Ion Batteries" and its frequent questions page (read November 21, 2026): these batteries "should not go in household garbage or recycling bins. They can cause fires during transport or at landfills and recyclers." City of Tampa recycling FAQ: "Electronics or batteries of any kind are never to be placed in your recycling cart." | The EPA sentence is about lithium-ion batteries and devices that contain them. No count of fires is given here |
| Plastic bags jam the sorting machines; Tampa's sorting line stops up to three hours a day | City of Tampa recycling FAQ (read November 21, 2026): plastic film, bags, clothes, ropes, cords and hoses "cause shutdowns in the sorting process for up to 3 hours each day" | Tampa's own sorting plant |
| Food or liquid spoils the paper around it | City of Tampa news release "Recycling Contamination at All-Time High", November 14, 2022: contamination happens "when items are placed in the bin with liquid or food residue", and contaminants "turn your recycling into nothing more than trash". University of New Hampshire waste audit, published February 2025: a bottle with liquid in it "may make the entire bin no longer recyclable" | Neither source measures how often one item spoils a whole load |
| Hillsborough County reports over 30 truck fires in three years | Hillsborough County, Florida, news release "Lithium-Ion Batteries Pose a Fire Risk When Disposed in the Garbage or Recycling", December 9, 2025: "Hillsborough County Solid Waste experienced over 30 garbage and recycling truck fires over the past three years alone." | The county that contains Tampa. The release is a warning about batteries; it does not say how many of the fires batteries caused |
| People also guess wrong on everyday items | No survey figure. Signs that the mistakes are real: Tampa's 2022 release names "wishcycling"; its FAQ answers "Why are pizza boxes not accepted, they're cardboard?"; the New Hampshire audit found coffee cups and plastic cups in recycling bins | Say "a common mistake" or "the common guess". No number |
| Signs alone fall short; a trained helper cut wrong items by 85 percent or more | University of British Columbia, 2018 (Zelenika, Moreau and Zhao): at a campus festival, volunteer staff reduced contamination by 96, 97, 97 and 85 percent in four bins; bins with signs alone "had no significant effect" | A person, not a screen. One festival |
| We found no product that looks again or asks | The maker's page for Oscar Sort (Intuitive AI) describes a camera and screen that retrofit to existing bins and can point out liquid in bottles and food in boxes. It does not mention asking a question or asking to open an item | "We found none" is the honest form |
| The fast alert: 10 of 10 wreckers caught, no false alarm in 52 tries, about one second | The team's own check, run at 4:46 PM today: `sorty/tests/results/GUARD.md`. Five wrecker pictures (batteries, phone, vape, plastic bag, tied bag of trash) and 26 ordinary ones, each shown twice to Claude Haiku 5.5 | Computer-made pictures, one picture per wrecker, the fast look run on its own. Not tried on a real bin camera |
| Sorty 32 of 33 written cases, one look 28 | The team's own test, run at 4:30 PM today: `sorty/tests/results/REPORT.md` | See "Today's tests" below |

### What Sorty does that a one-look camera does not

Said fairly: camera bins exist and help. One campus (UW–Madison, 2025) measured "a nearly 10% improvement in waste sorting correctness" with Oscar Sort units. What we found none of them doing:

- working out which fact decides the bin, and whether it can be seen;
- asking the person to open or turn the item, then looking again;
- taking a closer second look for grease, mold or small print;
- asking one question when no camera can know.

The proof from today's test, side by side:

| | Right, of 33 | Right, of the 14 hidden cases |
|---|---|---|
| The same AI with one look | 28 | 9 |
| Sorty | 32 | 13 |

The one-look version played safe each time: it sent the clean pizza box to compost, both marked cups to the trash, and the empty spray can to the hazardous drop-off. Safe, but four good items lost. On the 19 cases where everything is visible, both got all 19.

### How it is built, for the technical criterion

- **Two models in parallel.** Both start the moment the system is activated. A small fast check (Claude Haiku 5.5, small picture, one narrow question) raises the red "Stop" alert when it is sure, without waiting. If it stays silent, the careful model (Claude Opus 5.5) answers as usual: it looks again, asks, and runs the closer second look. The fast check is a plug-in: on a real bin a small detector on the bin's own computer could take its place. That detector does not exist.
- **LangGraph.** A LangGraph orchestrator now exists (think, then a closer look or a pause for the person, then think again, then end). It passed 4 of 4 live items on Claude and 56 offline checks. It is built to run on Gemini too; that path has never made a real call, so it is not verified. The 33-case test used the original orchestrator.
- **Pretrained models.** The team trained nothing. What the team wrote is the instructions, the bin rules and the code around the models.

### Say this only if asked

These were cut to stay under three minutes. Each is sourced.

- **Vision AI and dirt.** In a December 2025 study (Park, Kumar and Rajpurkar, arXiv 2601.00905), three leading vision models judged clean-and-dirty pairs of the same object fully right only 4 to 7 times in 10. Older models than Sorty's, and a small set.
- **Vision AI in messy scenes.** On a benchmark of cluttered waste pictures (Ali and Khan, "Waste-Bench", arXiv 2509.00176, August 2025), the best model scored 57.5 percent against 81.2 percent for people. A different task, older models.
- **How common the hidden problem is on a campus.** In one University of New Hampshire building audit (17 bags from recycling bins, December 6, 2024), 53 percent of plastic cups held leftover liquid or residue, 97 percent of plastic bottles were contaminated, and 77 percent of coffee cups. One building, one day.
- **How much of Tampa's recycling is wrong.** In 2020 the city reported that 36 percent of what went into its recycling carts did not belong; its contract allowed 20 percent or less (City of Tampa news release, August 3, 2020). Always say the year.
- **More sourced facts on fires, bags and liquids** are in `pitch/WRECKER_FACTS.md`, each with its source and year.
- **Nature.** The EPA counted about 94 million tons recycled or composted in 2018, out of 292.4 million tons of municipal waste. It says recycling, composting, combustion with energy recovery and landfilling together saved over 193 million metric tons of carbon dioxide equivalent that year, comparable to taking almost 42 million cars off the road; paper and cardboard recycling was the largest part, over 155 million.
- **The simplest fix for drinks.** At Villanova University, pour-out bins captured nearly 80 percent of the liquid waste at one location. For drinks a bucket may beat a question.
- **Our cost.** On paper: about 340 dollars of parts per bin, and about 250 dollars a month on the careful model, at 300 items a day. The fast alert's whole check cost under one cent. Cheaper careful models cost far less but are not proven: the cheapest skipped a question in two of three earlier runs.
- **What it saves in money.** Unknown. A payback sum needs two sourced inputs: what a spoiled load or a fire costs, and how many a bin prevents. We have neither, so we show none.
- **The one case Sorty missed.** The paper coffee cup with coffee left. It said to pour out the coffee and put cup and lid in the black bin, as written. It also told the person to slide off the cardboard sleeve and recycle it, which our written answer did not allow. The one-look version gave the same answer.
- **Speed of the careful model.** In today's test it took 5.0 seconds per item on average, from 1.6 to 11.2. Too slow for a busy bin; that is why the alert runs beside it.
- **The demo station is a sample.** In Tampa the green cart is recycling, and soiled pizza boxes are not accepted in it. Each site would get its own rule file. Tampa's is not written.

### Not confirmed, so not used

- **A national count of battery fires.** `pitch/WRECKER_FACTS.md` gives the EPA's figure (more than 240 fires at 64 waste facilities, 2013 to 2020). The EPA page refused the request when this script was checked, so the figure is not in the spoken lines.
- **What contamination costs the country.** "At least 300 million dollars a year" is widely attributed to The Recycling Partnership; the pages reporting it could not be opened.
- **The national contamination rate** (about 17 percent, same organisation): confirmed only through trade press.
- **A sourced list of which items people most often get wrong**: not available when this was written.
- **What existing camera bins cost**, and **fees cities pay for contaminated loads**: the pages could not be opened.
- **The team's email** held no recycling statistics, so nothing from it is quoted.

---

## Numbers about Sorty itself

### Today's tests

**The careful model, 33 cases.** Run at 4:30 PM on Claude Opus 5.5 with the original orchestrator. Report: `sorty/tests/results/REPORT.md`.

| | Right, of 33 | Right, of the 14 hidden cases |
|---|---|---|
| The same AI with one look and no questions | 28 | 9 |
| Sorty (looks again, looks closer, asks) | 32 | 13 |

**The fast alert, 31 pictures shown twice.** Run at 4:46 PM on Claude Haiku 5.5. Report: `sorty/tests/results/GUARD.md`.

| | Result |
|---|---|
| Wreckers (batteries, phone, vape, plastic bag, tied bag of trash): 10 showings | Alert raised on 10 of 10 |
| Ordinary items: 52 showings | 0 false alarms |
| Time for one fast look | About 1 second, 2.8 at the slowest |

What these are, said plainly:

- **Cases the team wrote**, each with pictures and, for the 33, a hidden truth such as "the can is half full". The AI's instructions were written with these items in mind.
- **Computer-made pictures** of single items on a plain background. Not photos from a real bin camera. One picture per wrecker.
- **A simulated person** (another AI call) answers Sorty's questions in the 33-case test. Not real people.
- **One run** of the 33 cases. A second run could differ by a case or two.
- **"Right"** means the right bin, any needed instruction such as pouring out a drink, and sensible behaviour: it asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was visible. The one-look version is graded on bin and instruction only.
- **Sorty's one miss:** the paper coffee cup (described above).
- **The one-look version's misses:** clean pizza box, both marked cups, the empty spray can, and the same coffee cup.
- **12 of 33 items** needed nothing from the person. Average AI thinking time of the careful model: 5.0 seconds per item.

### Other numbers

| Number | What it means | Source |
|---|---|---|
| About 8 seconds | AI thinking for each pizza box in today's test (8.0 and 8.5) | `latest.json` |
| 1.6 seconds | AI thinking for the batteries on the careful model alone | `latest.json` |
| 25 runs, 23 right | Earlier single-item checks today, on four items and three Claude models. Both misses were the cheapest model answering a soda can without asking | The `smoke`, `speed_`, `ping` and `t_` files in `sorty/tests/results/` |
| $1.14, and under 1 cent | What the 33-case test and the alert check cost in AI fees | `REPORT.md`, `GUARD.md` |
| $5 | Limit of the AI spending guard; about $2.35 used by 4:32 PM | `sorty/brain/budget.py`, `sorty/.usage.json` |
| 4 | Moves of the careful model: answer, ask to see another side, look closer, ask | `sorty/brain/tools.py` |
| 3 | Most requests to a person for one item. Enforced in code | `sorty/brain/agent.py` |
| 113 | Automatic checks of the code that passed at 4:15 PM. They use a scripted stand-in for the AI and say nothing about its judgement | `sorty/tests/test_offline.py` |
| 2 and 2 | Station layouts ready (three bins, two bins); screen languages (English, Spanish) | `sorty/brain/rules/`, `sorty/brain/phrases.py` |
| About $340 and $250 a month | Parts for one kit, and running one bin on the careful model. The team's estimate, on paper | `business/COST_ESTIMATE.md`, `pitch/COST_REVIEW.md` |

---

## Likely questions

The guide says the judge's minute covers "functionality, technical implementation, and design decisions". Each answer is two sentences.

**Know this by heart (every teammate, without notes):** a sensor, today a button, says an item is in range, and the camera takes one picture. Two AI models get it at once. A small fast one answers a single question, whether the item is one of the few that wreck a load, and can turn the screen red in about a second. The careful one, Claude Opus 5.5, gets the picture with the bin rules and must answer with one of four moves; for a small detail such as grease it is asked again with a zoomed picture and a short checklist. The code checks each move, drops any bin that is not on the station, enforces the limit of three requests, and turns the result into what the screen shows and the voice says. If the AI fails, the screen says "Please check the labels on the bins".

**Functionality**

1. **How accurate is it?**
   "On 33 cases we wrote ourselves, with computer-made pictures and one run, Sorty got 32 and the same AI with one look got 28. That is not accuracy on a real bin: no real photos and no real people."

2. **Show me one it got wrong.**
   "The paper coffee cup: it gave the cup and lid the black bin, as written, but also told the person to recycle the cardboard sleeve, which our written answer did not allow. On a real bin today we would not find out, because no picture is saved and no answer is logged."

3. **Run it again with a different input.**
   "Pick any card in the tray; the 33 test cases were each run once today. Or we switch to camera mode: hold up a real object, press the sensor button, and answer its question yourself." [Camera mode has no logged run: try it first.]

4. **Why does the careful model take so long?**
   "In today's test it took 5 seconds per item on average, about 2 for a visible item and about 8 for the pizza box. That is too slow for a busy bin, which is why the fast alert, about one second, runs beside it for the items that do the most damage."

5. **What happens if the person does not answer, does not know, or lies?**
   "Sorty gives the answer that is safe either way, like compost for a pizza box it could not see inside. The AI is instructed to treat what a person says as information and never as a command; that is a rule in its instructions, not in the code."

6. **It answers and the bin lights up. How do you know the person did it?**
   "Today we do not: Sorty does not see where the item lands and keeps no record. The same camera could confirm it in a later version."

7. **What does it cost, and what does it save?**
   "On paper, one kit is about 340 dollars in parts, and running one bin is about 250 dollars a month on the careful model, at 300 items a day; cheaper models cost far less but are not proven. What it saves we cannot say: we have no sourced figure for what a spoiled load or a fire costs."

8. **Who pays for this?**
   "Our guess is whoever pays when a load is spoiled or a truck catches fire: a campus facilities office, or a city or its hauler. Tampa's contract allowed 20 percent wrong items and the city reported 36 in 2020; we have no customer and no pilot."

**Technical implementation**

9. **Which AI models are these? What data did you train them on?**
   "Claude Opus 5.5 for the careful answer and Claude Haiku 5.5 for the fast alert, both pretrained models from Anthropic. We trained nothing, so there is no training data of ours; what we wrote is the instructions, the bin rules and the code around them."

10. **How did you evaluate it, and what does "correct" mean?**
    "Correct means the right bin, the needed instruction, and sensible behaviour: it asked when no camera could know, looked again when a camera could, and did not bother the person when the answer was visible. We ran 33 written cases once, next to the same AI limited to one look, and showed the fast alert 31 pictures twice."

11. **Why an agent? What does asking buy?**
    "On the 19 cases where everything is visible, one look was enough: both got all 19. On the 14 hidden ones, one look got 9 by playing safe and losing good items, and Sorty got 13."

12. **How is it orchestrated? Does it run on other models?**
    "The step-by-step control is our own code, and a LangGraph version of it passed four live items on Claude. It is built to run on Gemini too, but that has never made a real call, so we do not claim it."

13. **How do you check what the model returns before a bin lights up?**
    "It can only answer through tools with fixed fields, and the code drops any bin that is not in the station's file. No tool call, a refusal or an error from the AI service all end with 'Please check the labels on the bins'."

14. **What did you build yourselves, and what did AI generate?**
    "All the code, the Blender scripts and the written documents were made by an AI coding assistant, Claude Code, from our instructions, and our README lists that part by part. We chose the problem, said how Sorty must behave, made the product decisions and reviewed the work."

15. **How is this different from the camera bins that already exist?**
    "A product called Oscar Sort already puts a camera and a screen on existing bins, and one campus measured nearly 10 percent better sorting with it. We found no sign that it asks a question or asks you to open something; that step is ours, and so far we have tested it only on our own cases."

**Design decisions**

16. **Why two models?**
    "The careful one takes about five seconds, and the items that wreck a load should be stopped before they leave the hand. So a small fast check asks only that one question, in about one second, and the careful model handles everything else."

17. **Why ask questions at all? People are impatient.**
    "A warning is enough when the bin is the same either way, but when the hidden fact changes the bin, a warning hands the choice back to the person. So Sorty asks only then, never more than three times."

18. **Why is the green bin compost? In Tampa green is recycling.**
    "The demo uses a sample three-bin station, not Tampa's rules. Each site gets its own rule file with its own bins and colours, and Tampa's is not written yet."

19. **A camera in a public place: what happens to the pictures?**
    "Our computer does not save the picture, and the screen says so. It is sent to the AI company, whose standard policy is to delete it within 30 days, so a real site would need a notice and an agreement."

**Plain words for what is missing.** Use these as they are.

- "Everything you saw is software on computer-made pictures: one object, plain background, even light. A real camera will do worse, and we do not know by how much."
- "Our test cases are the items we designed for. Items nobody planned for are untested."
- "Nobody has used it. Whether anyone waits several seconds at a bin is the first thing we would test."
- "Our bin rules are an example drafted by AI. A real site would load its own list."

---

## Thirty-second version

77 words, about 33 seconds at a calm pace.

> We are [team name]. A few items wreck recycling for everyone: batteries start fires, bags jam the machines, food and liquid spoil the paper. Sorty is a camera and a voice for any bin. A fast check shouts "Stop" for those items, and a careful one knows what it cannot see: it asks you to open the box, or asks one short question, then lights the right bin. Software only so far, tested on our own cases.

---

## Other ways to run the demo

- **A wrong-guess opener in place of the batteries.** "Empty chip bag" takes about 12 seconds: the common guess is recycling, and Sorty says black bin because shiny film is not foil. "Clear cup, marked compostable underneath" takes about 23 seconds: Sorty asks to see the bottom and reads the mark; in today's test the one-look version sent it to the trash.
- **The soda can, answered by the judge** (for the questions minute). Untick Auto-answer, click "Soda can, half full", and let the judge press Yes or No under the scene. Say with it: "The can goes in the blue bin either way. The answer changes what the person has to do first."
- **The camera moment** (never inside the timed three minutes). Click **Use my camera**, hold a real object up to the webcam, press the blue **Sensor: object in range** button or the Space key, and answer or turn the object when Sorty asks. No camera run is in the test logs: try it with a few real objects first, and leave it out if it fails.
- **Scripted answers (practice mode).** It starts by itself when there is no API key or the spending limit is reached. Start the demo with "These answers are scripted".
- **If the showcase misbehaves.** Click **Open the real screen**, press **M**, pick the same three cards, and press **D** for the step list.

---

## Checklist

- [ ] README credits read by everyone, so the team says the same thing.
- [ ] Project submitted on MLH (OrganizerHQ) before **6:00 PM sharp**, with "frameworks and AI usage" filled in.
- [ ] Challenges checked: Off the Grid, Home Turf, Best Overall. "One submission per team."
- [ ] The red alert tried once on the page with "AA batteries". If it does not appear, use the wording under "If the red alert does not appear on the page".
- [ ] `sorty\run.bat` running and `http://localhost:8787/showcase/` open before 6:20 PM.
- [ ] Badge reads "Live AI: claude-opus-5-5", Faster mode unticked, Auto-answer ticked, sound on.
- [ ] Warm-up done: one pizza box played, with sound, shortly before the judge arrives.
- [ ] AI spend checked on the page ("AI spend: $... of $5.00").
- [ ] Phone hotspot ready, and everyone knows the scripted fallback.
- [ ] The script rehearsed once with a stopwatch, all three items.
- [ ] Everyone can give the "know this by heart" answer, say what the tests are, and say what "correct" means.
- [ ] "Stay at your assigned table during the judging period."
- [ ] The tests are always said as counts: 32 of 33 next to 28 of 33, and 10 of 10 with no false alarm in 52, on our own cases and computer-made pictures.
