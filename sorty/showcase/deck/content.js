/* Sorty pitch deck: ALL wording and numbers live here.
   Change text in this file only; layout and motion are in deck.css and deck.js.
   Each slide: id, layout, kicker, headline, body lines, figures (with source captions), notes (speaker notes),
   plus a few fields that belong to its layout (cards, steps, moves, branches, columns, sides).
   - "skip: true" on a slide leaves it out of the deck without deleting its wording.
   - A figure with "placeholder" instead of "value" is shown as a dashed "to fill in" tile.
   - An empty "source" is simply not shown: paste the origin in when it is known. */
window.DECK = {
  meta: {
    title: "Sorty",
    tagline: "The bin that looks twice, and asks.",
    team: "[team name]",
    demoUrl: "http://localhost:8787/showcase/",
    targetSeconds: 180
  },

  /* THE ONE FIELD for the measured alert numbers (shown inside the fast lane on the "lanes" slide).
     Source: sorty/tests/results/GUARD.md, run 21 Nov 2026 4:46 PM: Claude Haiku 5.5, all 31 test pictures shown twice. */
  alertMeasured: "10 of 10 wrecker showings caught. 0 false alarms in 52 ordinary showings.",

  flags: {
    /* true shows the orchestratorLine under the "lanes" slide. */
    orchestratorLine: true
  },
  orchestratorLine: "LangGraph orchestrator: 35 of 36 test cases right on Claude. Alert built for Jev, brain built for Gemini: both not yet run.",

  /* THE DECK IS FIVE SLIDES: problem, fail, built, lanes, gain. Everything marked "skip: true" further down
     is older material kept for reference; remove "skip: true" to show a slide again. */
  slides: [
    {
      /* 1. What's the problem. The wrecker cards have no source yet: paste the sourced statements from
         pitch/WRECKER_FACTS.md into "text" and "source". The two figures below are sourced. */
      id: "problem", layout: "cards",
      brand: "Sorty",
      kicker: "The problem",
      headline: "A few items wreck a whole load.",
      /* The gallery: 29 everyday items that are hard to choose a bin for, plus one question tile.
         Items with "wreck" light up red after a moment, with that word as their tag.
         Pictures are the Blender cut-outs in showcase/assets/items. */
      gallery: {
        caption: "Which bin? Every one of these is hard to choose. Seven of them can wreck the whole load.",
        items: [
          { image: "../assets/items/pizza_box_closed.png", label: "Closed pizza box" },
          { image: "../assets/items/coffee_cup_lid.png", label: "Paper coffee cup" },
          { image: "../assets/items/battery_aa.png", label: "Batteries", wreck: "fire" },
          { image: "../assets/items/cold_cup_side.png", label: "Clear cup" },
          { image: "../assets/items/chip_bag.png", label: "Chip bag" },
          { image: "../assets/items/soda_can.png", label: "Soda can" },
          { image: "../assets/items/plastic_bag.png", label: "Plastic bag", wreck: "jams" },
          { image: "../assets/items/carton_empty.png", label: "Juice carton" },
          { image: "../assets/items/greasy_napkin.png", label: "Used napkins" },
          { image: "../assets/items/glass_bottle_empty.png", label: "Glass bottle" },

          { image: "../assets/items/vape.png", label: "Vape", wreck: "fire" },
          { image: "../assets/items/clamshell_closed.png", label: "Takeout box" },
          { image: "../assets/items/pizza_box_open_greasy.png", label: "Greasy pizza box" },
          { image: "../assets/items/opaque_bottle.png", label: "Shampoo bottle" },
          { image: "../assets/items/clear_bottle_half_cola.png", label: "Half-full bottle", wreck: "spoils" },
          { image: "../assets/items/plastic_fork.png", label: "Plastic fork" },
          { image: "../assets/items/banana_peel.png", label: "Banana peel" },
          { image: "../assets/items/spray_can.png", label: "Spray can" },
          { image: "../assets/items/tied_bag.png", label: "Bag of trash", wreck: "spoils" },
          { image: "../assets/items/cold_cup_bottom_compostable.png", label: "Compostable cup" },

          { image: "../assets/items/pizza_box_open_clean.png", label: "Clean pizza box" },
          { image: "../assets/items/clear_bottle_empty.png", label: "Empty bottle" },
          { image: "../assets/items/clamshell_open_food.png", label: "Takeout box with food", wreck: "spoils" },
          { image: "../assets/items/cardboard_box_clean.png", label: "Cardboard box" },
          { image: "../assets/items/smartphone.png", label: "Phone", wreck: "fire" },
          { image: "../assets/items/pizza_box_open_leftovers.png", label: "Pizza box with leftovers" },
          { image: "../assets/items/cold_cup_bottom_pet.png", label: "Plastic cup" },
          { image: "../assets/items/pizza_box_open_moldy.png", label: "Moldy pizza box" },
          { image: "../assets/items/two_items_peel_bottle.png", label: "Peel and bottle" },
          { ask: "Which bin?" }
        ]
      },
      cards: [],
      /* Figures from pitch/WRECKER_FACTS.md (every source opened 21 Nov 2026). Others ready to swap in:
         { value: 36, suffix: "%", label: "of Tampa's recycling did not belong there. The contract allowed 20%.", source: "City of Tampa, news release, Aug 2020" }
         { value: 30, suffix: "+", label: "garbage and recycling truck fires in three years in Hillsborough County.", source: "Hillsborough County, news release, 9 Dec 2025" } */
      stats: [
        /* Matches the spoken line "over 30 truck fires in three years". The EPA figure is kept as an alternate:
           { value: 240, suffix: "+", label: "fires caused by lithium-ion batteries at 64 US waste facilities, 2013 to 2020.", source: "US EPA, lithium-ion battery page, updated Jul 2026" } */
        { value: 30, suffix: "+", label: "garbage and recycling truck fires in three years, reported by Hillsborough County in a warning about lithium batteries.", source: "Hillsborough County, news release, 9 Dec 2025" },
        { text: "3 h", label: "Up to 3 hours of sorting shutdowns a day in Tampa, caused by bags, film and other tanglers.", source: "City of Tampa, Recycling FAQs, updated Feb 2025" }
      ],
      foot: "Liquid and food residue can get a whole truckload rejected (City of Tampa, Recycling FAQs, 2025).",
      notes: "This is Sorty. Look at this wall of everyday items: for every one of them it is hard to choose the bin. But the biggest problem is not people unsure where paper goes. It is the few things, lit up in red, that wreck a whole load of recycling. Batteries, vapes and electronics start fires: the US EPA found more than 240 fires caused by lithium-ion batteries at 64 waste facilities. Plastic bags jam the sorting machines: Tampa says tanglers stop its sorting for up to 3 hours each day. And liquid and food can get a whole truckload rejected."
    },

    {
      /* 2. Why current efforts fail: three short points. */
      id: "fail", layout: "cards",
      kicker: "Why current efforts fail",
      headline: "People guess wrong. Nothing stops them.",
      /* The confusion research: what people believe or do. Every figure and source is copied from
         showcase/assets/confusion.json (pages opened 21 Nov 2026). Shown above the three cards. */
      stats: [
        { value: 55, suffix: "%", label: "of US adults thought compostable items recycle with cans and bottles", source: "Keep America Beautiful / The Harris Poll, 2025" },
        { value: 61, suffix: "%", label: "of US adults said flexible plastic can go in their curbside bin", source: "Republic Services Consumer Recycling Survey, 2022" },
        { value: 46, suffix: "%", label: "put disposable coffee cups in the recycling bin in a sorting study", source: "Barnett, Klotz, Hancock and Attari, The Conversation, 2023" },
        { value: 68, suffix: "%", label: "of young vape users threw empties in the trash; 13% in recycling", source: "Truth Initiative, 2022" },
        { value: 36, suffix: "%", label: "of US consumers throw batteries in the trash; 30% mix them with recyclables", source: "UL Standards & Engagement, 2024" }
      ],
      cards: [
        { big: "Signs", title: "made no clear difference.", text: "A trained helper at the bin cut wrong items by 85% or more.", source: "University of British Columbia, 2018 (Zelenika, Moreau and Zhao): one campus festival" },
        { big: "One look", title: "cannot see what is hidden.", text: "A one-look camera got 28 of 33 right, and 9 of the 14 hidden cases.", source: "Our test, 21 Nov 2026: same model, rules and pictures as Sorty" },
        { big: "Smart bins", title: "cost $10,000 or more each.", text: "One camera bin on sale: $10,000 to $15,000 per installation, plus yearly fees.", source: "Waste Dive, Jul 2025" }
      ],
      meters: [
        /* the one-look comparison (28 of 33; 9 of 14 hidden) now sits in the "One look" card above */
      ],
      foot: "Surveys are US-wide and bin rules differ from place to place. Our test: Blender-rendered pictures, one run.",
      notes: "People guess wrong at the bin, and the surveys say so. 55 percent of US adults thought compostable items go with cans and bottles. 61 percent said flexible plastic can go in the curbside bin. In one sorting study, 46 percent put coffee cups in recycling. And for the dangerous items: 68 percent of young vape users threw empties in the trash, and 36 percent of consumers throw batteries in the trash. What exists does not fix it. In one university trial signs made no clear difference, while a trained helper at the bin cut wrong items by 85 percent or more. A camera that looks once cannot see what is hidden: in our own test it got 28 of 33 right, and only 9 of the 14 cases where the answer is hidden. And the smart bins on sale are costly: one camera bin sells for 10 to 15 thousand dollars per installation, plus yearly fees."
    },

    {
      /* 3. What we built: the product visual. */
      id: "built", layout: "title",
      kicker: "What we built",
      headline: "Sorty",
      body: ["An instant alert for load-wreckers.", "A fast alert model says Stop in about a second, even for someone in a hurry. A careful check then finds the right bin, on any bin."],
      /* Three evidence groups under the picture. A line is a string, or { text, cite } where cite is shown in small print.
         Cheap: business/COST_ESTIMATE.md. Effective: sorty/tests/results (REPORT.md, REPORT_lg_full.md, GUARD.md), run 21 Nov 2026.
         Psychology: the README table "Designed around how people behave at a bin"; the three references are classic
         published findings cited from memory, not re-read today. */
      groups: [
        { title: "Cheap", big: "$340",
          lines: ["of parts per bin, on paper", "Camera bin on sale: $10,000 to $15,000 installed"],
          source: "Our estimate, seller prices of 21 Nov 2026; Waste Dive, Jul 2025" },
        { title: "Effective", big: "10 of 10",
          lines: ["load-wreckers caught, about 1 s each", "0 false alarms in 52", "Sorty 32 of 33; one look 28", "35 of 36 on LangGraph"],
          source: "Our tests, 21 Nov 2026: Blender-rendered pictures, one run" },
        { title: "Built on psychology", tone: "psy",
          lines: [
            { text: "One answer, never a list", cite: "Hick, 1952: more choices, slower decisions" },
            { text: "Arrow, colour, word and voice agree" },
            { text: "Eight words or fewer" },
            { text: "Always a short \"because\"", cite: "Langer, Blank and Chanowitz, 1978" },
            { text: "No blame" },
            { text: "Ends with a thank-you", cite: "Kahneman and colleagues, 1993: endings shape the memory" }
          ],
          source: "Published findings, cited from memory" }
      ],
      chips: ["Instant alert", "Looks again, and asks", "Fits any bin"],
      image: "img/hero.jpg",
      button: "Open the live demo",
      notes: "We built Sorty. First, an instant alert: a fast alert model says Stop in about a second for the few items that wreck a load, even when someone is in a hurry. Then a careful check that looks again and asks, for everything else, on any bin. It is cheap: about 340 dollars of parts per bin on paper, against 10 to 15 thousand dollars for a camera bin on sale. It is effective in today's tests, on computer-made pictures in a single run: the alert caught 10 of 10 load-wreckers with no false alarm in 52, Sorty got 32 of 33 where a one-look camera got 28, and 35 of 36 on the LangGraph orchestrator. And it is built on how people behave: one answer, never a list; arrow, colour, word and voice agree; eight words or fewer; always a short because; no blame; a thank-you at the end. Honest note: the three psychology references (Hick 1952; Langer, Blank and Chanowitz 1978; Kahneman and colleagues 1993) are classic published findings cited from memory, not re-read today. The University of British Columbia trial on the previous slide was read today. [Open the live demo here if there is time.]"
    },

    {
      id: "title", layout: "title", skip: true,
      kicker: "HackJam '26 · Off the Grid",
      headline: "Sorty",
      body: ["The bin that looks twice, and asks.", "A camera, a screen and a voice that fit on a bin and tell you where your trash goes."],
      chips: ["Stops what wrecks a load", "Looks again, and asks", "Lights the right bin"],
      image: "img/hero.jpg",
      notes: "We are [team name], and this is Sorty, in the Off the Grid track: a camera, a screen and a voice that fit on any bin."
    },

    {
      /* The lead problem. No numbers yet: sourced figures are being written to pitch/WRECKER_FACTS.md.
         Put each sourced statement into "text" and its origin into "source". Show no number without a source. */
      id: "wreckers", layout: "cards", skip: true,
      kicker: "The problem",
      headline: "A few items can wreck a whole load.",
      cards: [
        { title: "Batteries, vapes, electronics", text: "They can start fires in trucks and sorting plants.", source: "", tone: "bad", cutout: true, images: ["img/battery_aa.png", "img/vape.png"] },
        { title: "Plastic bags and film", text: "They jam the sorting machines.", source: "", tone: "bad", cutout: true, images: ["img/plastic_bag.png"] },
        { title: "Bagged trash", text: "Nobody can see what is inside a tied bag.", source: "", tone: "bad", cutout: true, images: ["img/tied_bag.png"] },
        { title: "Liquid and food", text: "They spoil the paper around them.", source: "", tone: "bad", cutout: true, images: ["img/clear_bottle_half_cola.png", "img/clamshell_open_food.png"] }
      ],
      foot: "Sorty's first job: spot these and say Stop before they go in.",
      notes: "The biggest problem is not people unsure where paper goes. It is the few things that can wreck a whole load: batteries, vapes and electronics that start fires in trucks and sorting plants, plastic bags that jam the sorting machines, bagged trash, and liquid and food that spoil the paper around them. [Add the sourced figures from pitch/WRECKER_FACTS.md.]"
    },

    {
      /* The second point: everyday wrong guesses. Each card: the common guess (cross), then Sorty's answer (tick).
         "claim" and "source" are empty until the research agent's sourced statements arrive
         (sorty/showcase/assets/confusion.json): paste the statement into claim and its origin into source.
         Colours: recycle #1F6FEB, compost #2DA44E, landfill #24292F, drop-off #B45309. */
      id: "confusion", layout: "flip", skip: true,
      kicker: "The second problem",
      headline: "People guess wrong on these.",
      wrongLabel: "Common guess", rightLabel: "Sorty",
      cards: [
        { image: "img/coffee_cup_lid.png", name: "Paper coffee cup", claim: "", source: "",
          wrong: { label: "Recycling", color: "#1F6FEB" }, right: { label: "Black bin", color: "#24292F" },
          why: "Pour out the coffee first. The cup has a plastic lining." },
        { image: "img/cold_cup_side.png", name: "Clear cup marked compostable", claim: "", source: "",
          wrong: { label: "Recycling", color: "#1F6FEB" }, right: { label: "Green bin", color: "#2DA44E" },
          why: "Once it has seen the mark underneath." },
        { image: "img/chip_bag.png", name: "Chip bag", claim: "", source: "",
          wrong: { label: "Recycling", color: "#1F6FEB" }, right: { label: "Black bin", color: "#24292F" },
          why: "Shiny film is not foil." },
        { image: "img/pizza_box_closed.png", name: "Greasy pizza box", claim: "", source: "",
          wrong: { label: "Recycling", color: "#1F6FEB" }, right: { label: "Green bin", color: "#2DA44E" },
          why: "It asks to see inside first." }
      ],
      foot: "Common guesses are our reading, not a survey. Right places follow this demo station's sample rules; every site has its own.",
      notes: "People also guess wrong on everyday items. A paper coffee cup has a plastic lining. A clear cup can be compostable. A chip bag is not foil. [Check each card against the test log before presenting.]"
    },

    {
      id: "today", layout: "cards", skip: true,
      kicker: "Why today's answers fall short",
      headline: "The best fix known is a person at the bin.",
      cards: [
        { title: "Signs", text: "In one university trial, signs made no clear difference to wrong items.", source: "UBC Science, 2018 (Zelenika, Moreau, Zhao)" },
        { title: "A helper at the bin", text: "Trained volunteers cut wrong items by 85 to 97 percent. But nobody can stand at every bin all day.", source: "UBC Science, 2018 (same trial, one festival)", tone: "good" },
        { title: "Camera-and-screen products", text: "They exist, and one campus reported nearly 10 percent better. We found no product that looks again or asks.", source: "UW-Madison Office of Sustainability, 2025 (the campus's own data)" },
        { title: "Sorting later, at the plant", text: "Too late for food and liquid: by then they are in the paper.", source: "Our reasoning. Tampa says residue can get a truckload rejected (city FAQ, 2025)" }
      ],
      foot: "Sorty tries to be that helper, on every bin, all day. Whether people treat a screen like a person is not shown yet.",
      notes: "Signs and one-look cameras help with what is visible. In one university trial signs made no clear difference, while a helper at the bin cut wrong items by more than 85 percent. We found no product that looks again or asks."
    },

    {
      id: "impact", layout: "figures", skip: true,
      kicker: "The impact",
      headline: "In Tampa, more than a third of the recycling did not belong there.",
      figures: [
        { value: 36, suffix: "%", label: "of what went into Tampa's recycling carts did not belong there", source: "City of Tampa, news release, Aug 2020" },
        { value: 20, suffix: "%", label: "or less: the most the city's recycling contract allowed", source: "City of Tampa, news release, Aug 2020" },
        { value: 53, suffix: "%", label: "of plastic cups in one campus building's recycling held leftover liquid or residue", source: "University of New Hampshire waste audit, Dec 2024" },
        { value: 94, suffix: "M", label: "tons recycled or composted in the United States in 2018", source: "US EPA, Facts and Figures (data through 2018)" },
        { value: 155, suffix: "M", label: "tons of CO2 equivalent saved by recycling paper and cardboard in 2018", source: "US EPA, Facts and Figures (data through 2018)" }
      ],
      foot: "Leftover food and liquid is one cause the city names.",
      notes: "In 2020 Tampa reported that 36 percent of what went into its recycling carts did not belong there. The contract allowed 20 percent. Wrong items turn recycling into trash."
    },

    {
      /* How the system works: one camera frame, two models started at the same moment.
         The measured alert numbers go into DECK.alertMeasured at the top of this file. */
      /* 4. How it works. */
      id: "lanes", layout: "lanes",
      kicker: "How it works: a multi-agent workflow",
      headline: "One camera frame. Four AI agents.",
      sensor: { title: "Sensor", text: "Item in range. Today: a button." },
      frame: { image: "img/battery_aa.png", text: "One camera frame" },
      /* The multi-agent workflow. Four AI agents, each with one job:
         1 the alert agent (fast lane), 2 the orchestrator (a LangGraph graph), and the two it calls:
         3 the inspector agent (closer look for grease, food, mold) and 4 the label agent (codes and marks).
         The orchestrator also turns to the person: one question, or "show me another side". */
      fast: { title: "1 · Alert agent", model: "Claude Haiku 5.5 · built for Jev",
              text: "Does this wreck a load? Also built for Jev.",
              end: "Stop!", endNote: "about 1 second" },
      careful: { title: "2 · Orchestrator agent", model: "Claude Opus 5.5 · LangGraph",
                 agents: [
                   { name: "3 · Inspector agent", does: "Closer look: grease, food, mold" },
                   { name: "4 · Label agent", does: "Reads codes and compostable marks" },
                   { name: "The person", does: "One question, or another view" }
                 ],
                 result: "32 of 33 test cases right.",
                 end: "One answer", endNote: "about 5 seconds" },
      measuredLabel: "Measured:",
      foot: "Our tests: Blender-rendered pictures, one picture per wrecker, not yet on a real bin camera.",
      notes: "The moment the system activates, two agents start on the same camera frame: this is a multi-agent workflow, four AI agents with one job each. The alert agent is a small, fast vision model with one narrow question: is this one of the few things that wreck a load? When it is sure, the screen turns red and says Stop, in about a second. Otherwise the orchestrator agent, a LangGraph graph, answers as usual: it asks the person or looks again, and it calls two more agents, an inspector for grease, food and mold, and a label reader. In our test the alert fired on 10 of 10 showings of load-wreckers, with no false alarm in 52 showings of ordinary items. Those are rendered pictures, not a real bin camera."
    },

    {
      /* 5. Potential benefits, with only sourced or measured numbers, and the honest limits as small print. */
      id: "gain", layout: "cards",
      kicker: "Potential benefits",
      headline: "What this could fix at scale.",
      /* Six benefits in a 3 by 2 grid. Red numbers are the problem as it is today (each with its source);
         green numbers are what a helper at the bin could change. Every figure is in pitch/WRECKER_FACTS.md,
         the "Evidence and sources" part of pitch/PITCH_3MIN.md, or business/COST_ESTIMATE.md. */
      cards: [
        { big: "430", title: "Fewer fires", text: "reported fires at waste and recycling sites in one year. Our alert caught 10 of 10 load-wreckers in today's test.", source: "Fire Rover count for 2024, US and Canada (Resource Recycling, Mar 2025); our test, 21 Nov 2026", tone: "bad" },
        { big: "3 h", title: "Sorting lines that keep running", text: "of shutdowns a day, at most, in Tampa's sorting: caused by bags, film and other tangling items.", source: "City of Tampa, Recycling FAQs, updated Feb 2025", tone: "bad" },
        { big: "36%", title: "Cleaner loads", text: "of what went into Tampa's recycling did not belong there. In today's test Sorty got 32 of 33 right; one look, 28.", source: "City of Tampa, news release, Aug 2020; our test, 21 Nov 2026", tone: "bad" },
        { big: "$10", title: "Lower costs", text: "to insure $100 of recycling plant, up from under 20 cents. Fewer fires could ease that.", source: "NWRA and RRS, news release, Jan 2024", tone: "bad" },
        { big: "85%", title: "A helper at every bin", text: "fewer wrong items, or more, with a trained helper at the bin. Signs alone made no clear difference.", source: "University of British Columbia, 2018 (one campus festival)", tone: "good" },
        { big: "$340", title: "Fits the bins already there", text: "of parts per bin, on paper. A camera bin on sale today costs $10,000 to $15,000 per installation.", source: "Our estimate, seller prices of 21 Nov 2026; Waste Dive, Jul 2025", tone: "good" }
      ],
      foot: "Limits: this is potential, not results. Our test pictures are Blender renders, one run. Not yet on a real bin; no hardware built.",
      notes: "At scale this goes after a very big problem: 430 reported fires at waste and recycling sites in one year, Tampa's sorting stopped for up to three hours a day by tangling items, and in 2020, 36 percent of what went into Tampa's recycling did not belong there. Sorty could mean fewer fires, sorting lines that keep running, cleaner loads and lower costs, by putting a helper at every bin for about 340 dollars of parts on the bins already there. That is potential, not a result: our tests used computer-made pictures, and nothing has been on a real bin yet. Thank you."
    },

    {
      id: "moves", layout: "moves", skip: true,
      kicker: "The careful lane",
      headline: "It knows what it cannot see.",
      moves: [
        { name: "Answer now", when: "Everything is visible", example: "Clear bottle with cola: \"Pour it out, then blue bin.\"", image: "img/clear_bottle_half_cola.png" },
        { name: "Look again", when: "A camera could see it, just not from here", example: "Closed pizza box: \"Open the box and show me inside.\"", image: "img/pizza_box_closed.png" },
        { name: "Closer look", when: "In view, but subtle", example: "Grease or a shadow? A second, focused look at a zoomed picture.", image: "img/pizza_box_open_greasy.png" },
        { name: "Ask", when: "No camera can know", example: "Soda can: \"Is there liquid inside?\"", image: "img/soda_can.png" }
      ],
      foot: "At most three requests per item. Then it must answer.",
      notes: "One picture cannot always tell. Sorty knows what it cannot see, and it has four moves: answer, ask to see another side, look closer, or ask one short question. What it learns goes back to the AI, three requests at most."
    },

    {
      id: "pizza", layout: "compare", skip: true,
      kicker: "Run live today",
      headline: "Same closed box. Two different bins.",
      start: { image: "img/pizza_box_closed.png", say: "\"Open the box and show me inside.\"" },
      branches: [
        { image: "img/pizza_box_open_greasy.png", finding: "Closer look: heavy grease on about 60 to 65% of the inside", bin: "compost", color: "#2DA44E", say: "Green bin, in the middle." },
        { image: "img/pizza_box_open_clean.png", finding: "Closer look: no grease", bin: "recycle", color: "#1F6FEB", say: "Blue bin, on your left." }
      ],
      foot: "Run on the live AI, on rendered pictures of the box. Not real photos.",
      notes: "Here is the same closed box twice. Greasy inside: the closer look reports heavy grease and the green bin lights up. Clean inside: no grease, blue bin. One picture could not tell these two apart."
    },

    {
      id: "demo", layout: "demo", skip: true,
      kicker: "Live demo",
      headline: "Watch it decide.",
      button: "Open the live demo",
      body: ["Greasy pizza box, then the clean one.", "Soda can: you press Yes or No.", "Camera mode: hold up a real object."],
      foot: "Average thinking time in our test: 5.0 seconds per item.",
      video: "img/turntable.mp4", poster: "img/hero.jpg",
      notes: "Open the demo. Pick the greasy pizza box, then the clean one. Talk over the wait: it cannot see inside, so it asks. Run one item before the judges arrive so the warm-up is over."
    },

    {
      /* The team's own test, finished 21 Nov 2026 4:30 PM: sorty/tests/results/REPORT.md.
         A side with "value: null" shows as a dashed "to fill in" tile. */
      id: "results", layout: "versus", skip: true,
      kicker: "The evidence",
      headline: "The same 33 cases, two ways.",
      total: 33, unit: "of 33 right",
      sides: [
        { name: "Sorty", detail: "Looks, looks again, looks closer, or asks.", value: 32, tone: "good",
          sub: "13 of 14 where the answer is hidden in the first picture" },
        { name: "One-look camera", detail: "Same model, same rules, same pictures. One look, no questions.", value: 28,
          sub: "9 of 14 where the answer is hidden in the first picture" }
      ],
      foot: "Our own test, 21 Nov 2026: Blender renders, one run, not yet tested on a real bin. Average thinking time 5.0 s per item.",
      notes: "We ran the same 33 written cases two ways: same model, same rules, same pictures. A camera that looks once got 28 right. Sorty got 32. The whole difference is in the hidden cases: 13 of 14 against 9 of 14. These are computer-made pictures and one run, so it is a first check, not a field result."
    },

    {
      id: "benefits", layout: "cards", skip: true,
      kicker: "The benefits",
      headline: "A helper at the bin that never goes home.",
      cards: [
        { title: "Stops what wrecks a load", text: "A fast model watches for the few items that wreck a load and turns the screen red in about a second.", source: "Our test, 21 Nov 2026: 10 of 10 alerts, rendered pictures", tone: "bad" },
        { title: "One answer, three ways", text: "Voice, a big arrow and one lit bin say the same thing, with one short reason.", image: "img/screen_verdict.jpg" },
        { title: "Looks again, and asks", text: "It looks first. It asks one short question when no camera could know. Never more than three requests." },
        { title: "Fits the bins already there", text: "A camera, a screen and a speaker on a pole. Local rules are plain sentences in one file per site.", image: "img/retrofit.jpg" }
      ],
      notes: "The benefit today: an instant alert for the few items that wreck a load, and for everything else one clear answer with a reason, on any bin layout."
    },

    {
      id: "potential", layout: "figures", skip: true,
      kicker: "The potential",
      headline: "Cheap to try on a real bin.",
      figures: [
        { text: "85 to 97%", label: "fewer wrong items with a trained helper at the bin, in one trial. Sorty aims to be that helper; not shown yet", source: "University of British Columbia, 2018, one festival" },
        { prefix: "$", value: 340, label: "of parts for one kit: priced today, not yet built, no labour or support", source: "Our cost estimate, seller prices of 21 Nov 2026" },
        { prefix: "$", value: 250, label: "a month per bin for the AI model in the demo, at 300 items a day. Cheaper models are not proven", source: "Our cost estimate" }
      ],
      foot: "The whole first experiment is a laptop and a webcam.",
      notes: "If it works on real bins, it could do the job of the trained helper who, in one university trial, cut wrong items by 85 percent or more. On paper one kit is about 340 dollars of parts, not yet built."
    },

    {
      id: "status", layout: "split", skip: true,
      kicker: "Honest status",
      headline: "The station is virtual. The software is real.",
      columns: [
        { title: "Real today", tone: "good", lines: [
          "The four moves, end to end, on the live AI",
          "32 of 33 written test cases right, on rendered pictures",
          "Instant alert: 10 of 10 load-wreckers, no false alarm, on rendered pictures",
          "LangGraph orchestrator, verified on Claude",
          "The virtual prototype runs the real screen software",
          "A spending cap and a practice mode"
        ] },
        { title: "Not yet", tone: "open", lines: [
          "A physical unit",
          "A real camera on a real bin",
          "Real people using it",
          "The Gemini path: written, not verified"
        ] }
      ],
      notes: "The station is virtual today; the software is real. Our test pictures are computer-made, so the result is a first check, not a field accuracy number. We built this today with an AI coding assistant; our README says what it wrote."
    },

    {
      id: "close", layout: "close", skip: true,
      kicker: "Next",
      headline: "Sorty",
      body: ["The bin that looks twice, and asks.", "Next step: one kit on one campus bin, and count what lands in the wrong bin with and without it."],
      thanks: "Thank you",
      image: "img/front.jpg",
      notes: "Today's test, on computer-made pictures: Sorty got 32 of 33 written cases; the same AI with one look got 28. No real camera, no real people, no hardware yet. Thank you."
    },

    /* ---------- kept but switched off (remove "skip: true" to show them) ---------- */
    {
      id: "hidden", layout: "statement", skip: true,
      kicker: "The problem",
      headline: "The fact that decides the bin is often hidden.",
      body: ["Is this pizza box greasy inside?", "Is this can empty?", "A sign cannot see your item. One photo cannot see inside it."],
      quote: { text: "Contamination can also happen when items are placed in the bin with liquid or food residue.", source: "City of Tampa news release, 14 Nov 2022" },
      items: [
        { image: "img/pizza_box_closed.png", label: "Greasy inside?" },
        { image: "img/soda_can.png", label: "Empty?" },
        { image: "img/coffee_cup_lid.png", label: "Coffee left?" }
      ],
      notes: "The answer is often hidden. Is this pizza box greasy inside? Is this can empty? A sign cannot tell, and one picture cannot tell either."
    },

    {
      id: "system", layout: "pipeline", skip: true,
      kicker: "How the system works",
      headline: "From a held-up item to one clear answer.",
      steps: [
        { title: "Sensor", text: "Notices an item in range. Today a button stands in for it." },
        { title: "Camera", text: "Takes one picture." },
        { title: "AI brain", text: "Works out which facts decide the bin, and whether it can see them." },
        { title: "One of four moves", text: "Answer now, look again, closer look, or ask. What it learns goes back to the AI. At most three requests." },
        { title: "One answer", text: "Voice, screen and the lit bin, with a short reason." }
      ],
      foot: "What holds it together: limits in the code (three requests, only real bins, a spending cap, a \"check the labels\" fallback) and bin rules in one file per site.",
      notes: "A sensor notices an item; today a button stands in for it. The camera takes one picture. The AI works out which facts decide the bin and whether it can see them. Then it makes one of four moves, and what it learns goes back to the AI, three requests at most. Voice, screen and the lit bin give one answer with a short reason."
    }
  ]
};
