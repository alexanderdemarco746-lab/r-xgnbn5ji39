# Sorty: slide content for the presentation deck

Exactly five slides. The live demo runs on the showcase page between slides 4 and 5. The speaker notes are the exact spoken lines from `pitch/PITCH_3MIN.md`: together with the demo lines they are the whole script, 364 words, about 2:50.

Every figure has a source caption. Figures marked "team" come from the team's own tests or estimate. Checked on November 21, 2026.

---

## Slide 1. What's the problem

- **Kicker:** The problem
- **Headline:** A few items wreck the whole load
- **Gallery (added 5:08 PM at the team's request):** a wall of 29 everyday items that are hard to choose a bin for, plus a "Which bin?" tile. Each carries a "?" that keeps changing between the three bin colours. After a moment the seven load-wreckers light up red with a tag:
  - Batteries, vape, phone: FIRE
  - Plastic bag: JAMS
  - Half-full bottle, takeout box with food, bag of trash: SPOILS
- **Caption under the headline:** Which bin? Every one of these is hard to choose. Seven of them can wreck the whole load.
- **Figures:**
  - **Over 30 truck fires in 3 years** : garbage and recycling trucks, in a county warning about batteries. Hillsborough County Solid Waste, news release, December 2025.
  - **Up to 3 hours a day** : Tampa's sorting line stopped by tangling items. City of Tampa recycling FAQ, read November 2026.
  - **36%** : of what went into Tampa's recycling carts did not belong. City of Tampa news release, August 2020.
- **Speaker notes:**
  > We are [team name], and this is Sorty, in the Off the Grid track. A few items wreck recycling for everyone: batteries start fires, plastic bags jam the sorting machines, and food or liquid spoils the paper around it. People also guess wrong on everyday items.
  >
  > Hillsborough County reports over 30 truck fires in three years; Tampa says tangling items stop its sorting line up to three hours a day.

---

## Slide 2. Why current efforts fail

- **Kicker:** Today's answers
- **Headline:** Signs and one-look cameras fall short
- **Lines:**
  - Signs alone: no significant effect in a university trial
  - One look misses what is hidden
  - Nothing we found looks again or asks
- **Figures:**
  - **9 of 14** : hidden cases the same AI got right with one look. Sorty got 13. Team's test, computer-made pictures, November 21, 2026.
  - **85 to 97%** : fewer wrong items with a trained helper at the bin, where signs alone changed nothing. University of British Columbia, 2018, one festival.
- **Speaker notes:**
  > Signs alone fall short, and a camera that looks once misses what is hidden. We found no product that looks again or asks.

---

## Slide 3. What we build

- **Kicker:** Sorty
- **Headline:** A fast alert and a careful second look
- **Lines:**
  - A camera, a screen and a voice for any bin
  - Fast model: "Stop!" for the items that wreck a load
  - Careful model: looks again, looks closer, asks
- **Figures:**
  - **10 of 10** : wrecker showings caught by the fast alert. Team's check, five computer-made pictures shown twice, November 21, 2026.
  - **0 of 52** : false alarms on ordinary items. Same check.
  - **About 1 second, against 5** : the fast look, against the careful answer on average. Same check and the team's 33-case test.
- **Speaker notes:**
  > So we built Sorty: a camera, a screen and a voice for any bin, with two AI models. A small fast one only asks: will this wreck the load?
  >
  > Measured today on our pictures: 10 of 10 wreckers caught, no false alarm in 52 tries, about one second, against five for the careful model.

---

## Slide 4. How it works

- **Kicker:** Under the hood
- **Headline:** One picture, two models, one answer
- **Pipeline, five steps** (short labels for the animation):
  1. **Sensor** : item in range (a button, for now)
  2. **Camera** : one picture
  3. **Two AI models** : fast alert and careful model, started together
  4. **Four moves** : answer, look again, look closer, ask (three requests at most)
  5. **One answer** : a short reason, and the right bin lights up
- **Lines:**
  - The limits live in the code
  - Bin rules: one file per site
- **Figures:**
  - **4** : moves of the careful model.
  - **3** : requests to a person at most, per item. Enforced in the code.
- **Speaker notes:**
  > How it works: a multi-agent workflow. A sensor notices an item; the camera takes one picture, and two agents start at once: the alert agent and the orchestrator, a LangGraph graph. The orchestrator finds the deciding fact, then picks one of four moves: answer, ask to see another side, call an inspector agent for a closer look, or ask one question. Then one answer with a reason, and the right bin lights up.

---

## Slide 5. Potential benefits

- **Kicker:** Why it matters
- **Headline:** A helper at every bin, all day
- **Lines:**
  - Today: one clear answer with a reason
  - Any bin layout, English or Spanish
  - Not yet tested on a real bin
- **Figures:**
  - **32 of 33, against 28** : Sorty, against the same AI with one look. Team's test, 33 written cases, computer-made pictures, one run, November 21, 2026.
  - **85 to 97%** : fewer wrong items with a trained helper at the bin. University of British Columbia, 2018.
  - **About $340, and $250 a month** : parts for one bin, and running it on the careful model. Team's estimate on paper; cheaper models are not proven.
- **Speaker notes:**
  > Today: one clear answer with a reason, in about a second for the dangerous items.
  >
  > At scale: fewer fires, sorting lines that keep running, cleaner loads, lower costs. In one university trial, a trained helper at the bin cut wrong items by 85 percent or more.
  >
  > Today's test, computer-made pictures: Sorty 32 of 33 written cases, one look 28. No real camera, no real people, no hardware yet. Thank you.

---

## Live demo (showcase page, between slides 4 and 5; not a slide)

Three cards, in this order: "AA batteries", "Pizza box, greasy inside", "Pizza box, clean inside". Spoken lines:

> Live now. Batteries: the common guess is the trash.
>
> The fast model caught it at once.
>
> Now a closed pizza box. The careful model, Claude Opus 5.5, asks to look inside, then takes a closer second look.
>
> An AI assistant wrote the code from our instructions.
>
> The same closed box, clean inside.
>
> Under the hood, the code holds the limits: three requests, real bins only, a spending cap, and "check the labels" if the AI fails. Bin rules are one file per site.
>
> No grease: blue bin. One picture could not tell these two apart.

---

## Notes for whoever builds the deck

- **Do not add** an accuracy percentage, a market size, a money saving, a count of battery fires or a competitor's price. None has a source the team could open.
- **LangGraph** stays off the slides. If asked: it passed four live items on Claude and is built to run on Gemini too, not yet verified.
- **Everyday wrong guesses**, if slide 1 has room for one small line: paper coffee cup, chip bag, greasy pizza box. No number: there is no survey behind them.

## Sources for the figures

- Hillsborough County, Florida, "Lithium-Ion Batteries Pose a Fire Risk When Disposed in the Garbage or Recycling", December 9, 2025: https://hcfl.gov/newsroom/2025/12/09/lithium-ion-batteries-pose-a-fire-risk-when-disposed-in-the-garbage-or-recycling
- City of Tampa, recycling FAQ: https://www.tampa.gov/solid-waste/programs/recycling-and-waste-reduction/faqs
- City of Tampa, "City of Tampa Announces New Recycling Contract", posted August 3, 2020: https://www.tampa.gov/news/city-tampa-announces-new-recycling-contract
- University of British Columbia, June 13, 2018, on Zelenika, Moreau and Zhao: https://science.ubc.ca/news/recycling-may-be-confusing-volunteers-help-get-it-right
- US EPA, "Used Lithium-Ion Batteries": https://www.epa.gov/recycle/used-lithium-ion-batteries
- The team's tests: `sorty/tests/results/REPORT.md` (33 cases) and `sorty/tests/results/GUARD.md` (fast alert). The team's cost estimate: `business/COST_ESTIMATE.md`.
