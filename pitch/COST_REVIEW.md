# Review notes on `business/COST_ESTIMATE.md`

Reviewed 2026-11-21, about 3:00 PM. I did not edit the estimate.

**Bottom line:** the arithmetic is right everywhere, and every seller price I re-opened matched. The two headline figures can be said out loud, as long as they keep their conditions: about **$340 in parts** for one kit, and about **$13 a month** to run one bin *on the cheapest AI model*. The weak points are assumptions, not sums.

**Update, 4:15 PM.** After this review, three models were run on a few items with the live AI (logs in `sorty/tests/results/`).

- The cheapest model (Haiku 5.5) answered the soda can without asking in two of its three runs. So the "$13 a month" figure belongs to a model that is not proven good enough, and it should never be quoted without the figure for the default model, about $254.
- The mid model (Sonnet 5.5) was right on all nine of its runs, on three items.
- Measured cost per item on the default model was 1 to 5 cents, which fits the estimate's 2.75 cents.

## What I checked and found correct

- **Every sum, recomputed line by line.** Tier A parts add up to $340.35, tier B to $701.29, tier C to $874.29. The "same as tier A" block ($54.40) and the "same extras as tier B" block ($371.30) are right. Labor is 6 hours at $30, $180.
- **AI cost per item.** Haiku 0.0693 cents, Sonnet 1.373 cents, Opus 2.746 cents: all three follow from the stated token counts and prices. The monthly table (100, 300, 500 items a day) is right in every cell.
- **Totals and comparisons.** $12.80 and $135.13 a month, the 10-kit rows, the yearly AI fees ($75, $1,480, $2,970), the "20 times" and "40 times" ratios, and the payback sums in section 5 are all right.
- **Electricity.** 15 watts is 10.8 kilowatt-hours a month; at 14.47 cents that is $1.56.
- **Prices I re-opened on the sellers' own pages today (all matched):**
  - Raspberry Pi 5 2GB, $77.50 at CanaKit and at PiShop.us (out of stock at PiShop.us, as the estimate says)
  - Touch Display 2, $81.95
  - Camera Module 3, $29.25
  - 27 W power supply, $12.95
  - USB speaker, $12.50
  - LED strip, $19.95
  - 5 V 4 A supply, $14.95

  Together these are $249 of the $340, about three quarters of tier A by value.
- **AI prices, on Anthropic's pricing page today.** Haiku 5.5 $0.10 in, $0.50 out, $0.01 cached. Sonnet 5.5 $2, $10, $0.10. Opus 5.5 $4, $20, $0.20. All as the estimate states.

## What is wrong, misleading or unsupported

1. **The headline hides the default model.** Sorty uses Opus 5.5 unless someone changes one setting. As shipped today, one bin at 300 items a day would cost about **$254 a month** ($247.14 + $1.56 + $5), not $13. The estimate says this in section 5 but not at the top.
2. **"Cheapest sensible" is not yet shown to be sensible.** When this review was written, nobody had tested whether Haiku 5.5 sorts correctly; see the update above. The $13 figure stands only if it does.
3. **The top summary compares two different kits.** "$13 with Haiku or $135 with Sonnet" sets tier A against tier B. On the same tier A kit, Sonnet would be about $130.
4. **Token counts are an estimate, not a measurement.** The estimate says so. My own count from the real prompt sizes gives about 6,400 to 6,900 input tokens per item, against the estimate's 6,100. That would make the Haiku AI fee $7 to $8 a month, not $6.24. Small.
5. **Two billing effects are left out, and they pull in opposite directions.**
   - Sorty writes each request to the prompt cache, and cache writes are billed at 1.25 times the input price ($0.125 against $0.10 on Haiku). That can add up to about 20% to the input cost.
   - On a busy bin, Sorty's fixed instructions (about 3,300 tokens) would be read back from the cache at one tenth of the price, which lowers the cost.
6. **Output may be too low for the bigger models.** The model's thinking is billed as output. The estimate flags this itself. On Haiku even three times the output adds under $4 a month; on Sonnet and Opus it could add a lot.
7. **Putting 4 to 6 together:** a pessimistic Haiku case comes to about $20 a month, so the honest range is **$13 to $20**. The $135 (Sonnet) and Opus figures are less certain than they look.
8. **300 items a day has no source.** It is a round assumption. At 100 a day the total is about $9 a month, at 500 about $17.
9. **Prices with no source, or a weak one:**
   - case extras beyond the filament (part of the $30)
   - power strip, cable seals and bolts ($15)
   - the DisplayPort adapter ($14; the estimate says its page would not load)
   - the solid-state drive ($89.99, from a price tracker's home page, not a product page)
   - the cellular modem (no price at all)
   - labor rate and hours (assumption)
   - 15% yearly upkeep (assumption)
   - data per item (estimate)
10. **Tier B rests on sale prices.** At regular prices the mini PC is $110 more and the webcam $15 more, so tier B would be about $826, not $701.
11. **"Cheapest that works" is unproven.** No unit has been built.
    - The tier A case is a 3D print, so it is for indoor use only.
    - The program that turns Sorty's answer into LED colours does not exist yet (the estimate says so). Without it the bins do not light up.
    - The estimate warns that voice input may not work in the Pi's browser. It does not mention that the spoken voice may also be poor or missing there. That is the product's main output and needs a test.
12. **Shipping and sales tax are left out** (stated). Tier A comes from four stores (CanaKit, PiShop.us, Adafruit, Prusa), so four shipping charges.
13. **Dates.** All 46 sources carry one date, 2026-11-21, which is fine for today. Sale prices can end at any time.
14. **Competitor prices are not verified by me.** The Waste Dive page behind the Oscar Sort figures refused my request, so I could not read it. I left those figures out of the pitch.
15. **Tier C is a paper idea.** The estimate says so clearly. Do not quote it.

## Figures safe to use in the pitch

| Figure | Say it as | Conditions that must travel with it |
|---|---|---|
| $340 | "about 340 dollars in parts for one kit" | Cheapest version, indoor case, prices of 2026-11-21, no tax, shipping or labor, nothing built |
| $13 a month | "about 13 dollars a month to run, on the cheapest AI model" | 300 items a day, site Wi-Fi, that model's accuracy untested, estimate not measured; honest range $13 to $20 |
| $254 a month | "about 250 dollars a month on the model the software uses today" | Say it if asked about running cost, so the $13 does not mislead |
