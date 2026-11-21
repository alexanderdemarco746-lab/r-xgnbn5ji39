# Sorty cost estimate

- **One kit:** about **$340** in parts for the cheapest version that works (tier A, Raspberry Pi), or about **$700** for the sturdier one (tier B, mini PC), plus about $180 of labor per kit if it is paid (assumption).
- **Running cost per bin, per month:** about **$13** with the cheapest AI model (Claude Haiku 5.5), or about **$135** with the mid model (Claude Sonnet 5.5), at 300 items a day.
- **Biggest cost driver:** the choice of AI model, not the hardware. Per item, Sonnet costs about 20 times as much as Haiku, and Opus (the software's default today) about 40 times.

Prices are in US dollars, checked on 2026-11-21, before tax and shipping. Numbers in [brackets] point to the Sources list. "Estimate" is a figure we worked out; "assumption" is a choice you can change. Nothing has been built or tested on real hardware. A memory-chip shortage raised prices in 2026 (Pi 5 2GB to $77.50 in October [1], Jetson kit from $249 to $399 in July [2]), so recheck before ordering.

## 1. Hardware for one kit

### Tier A: cheapest that works (Raspberry Pi 5)

| Part | Price | Seller and notes |
|---|---:|---|
| Raspberry Pi 5, 2GB | $77.50 | CanaKit, in stock [3]. Out of stock at PiShop.us [4] |
| Official 27 W power supply | $12.95 | PiShop.us [5] |
| microSD card, 32GB, with Raspberry Pi OS | $19.95 | PiShop.us [6] |
| Active Cooler | $11.95 | CanaKit [7]. Up to $13.50 elsewhere |
| Camera Module 3 | $29.25 | PiShop.us [8] |
| Camera cable for the Pi 5 | $3.95 | PiShop.us [9] |
| Touch Display 2, 7-inch | $81.95 | PiShop.us [10]. $87.95 at CanaKit [11]; list price $60 [12] |
| Mini USB speaker | $12.50 | Adafruit [13] |
| Mini USB microphone | $5.95 | Adafruit [14] |
| LED strip, 2 m (WS2812B type) | $19.95 | Adafruit [15] |
| Raspberry Pi Pico, drives the LEDs | $4.00 | Adafruit [16] |
| Level shifter chip | $1.50 | Adafruit [17] |
| 5 V power supply for the LEDs | $14.95 | Adafruit [18] |
| Cables and small parts | $14 | Estimate from Adafruit list prices [19] |
| Enclosure and pole mount | $30 | Estimate: 3D-printed case (half a $23.99 filament spool [20]), clamps, bolts |
| **Subtotal** | **$340** | |
| Optional: wake sensor | $3.95 or $14.95 | Not in subtotal; see "Optional extras" |

**Why 2GB:** the AI runs in the cloud; the Pi only shows one web page and runs a small server. 1GB ($45) is too tight for a browser; 4GB is $110 if 2GB proves slow [21]. To test: voice input was built for Chrome and Edge and may not work in the Pi's browser; the touch buttons would.

### Tier B: sturdier (fanless mini PC)

| Part | Price | Seller and notes |
|---|---:|---|
| Fanless mini PC, MeLE Quieter 4C SE (Intel N150, 8GB, 128GB, no operating system) | $329.99 | MeLE store; sale price, regular $439.99 [22] |
| Logitech C920s webcam with microphones | $54.99 | Logitech; special price, regular $69.99 [23] |
| Waveshare 10.1-inch touchscreen monitor | $114.95 | PiShop.us [24]. $96.99 direct from Waveshare [25] |
| Logitech S150 USB speakers | $19.99 | Logitech [26] |
| LED parts, cables and small parts | $54.40 | Same as tier A |
| Lockable weather-resistant plastic box, 14 x 11 x 5 inch | $61.99 | Altelix [27]. Sale price $49.59; stock unclear |
| Pole mount kit for the box | $24.99 | Altelix [28] |
| Pole mount for the screen | $24.99 | VIVO [29] |
| Power strip, cable seals, bolts | $15 | Estimate |
| **Subtotal** | **$701** | |
| Optional: wake sensor | $3.95 or $14.95 | Not in subtotal; see "Optional extras" |

### Tier C: no cloud fees (NVIDIA Jetson)

**Not built, not tested.** This tier would run a small open-source vision model on the kit instead of calling Claude. Its accuracy and speed are unknown.

| Part | Price | Seller and notes |
|---|---:|---|
| NVIDIA Jetson Orin Nano Super Developer Kit | $399.00 | SparkFun, in stock [30]. Was $249 until July 2026 [2] |
| Storage drive (NVMe SSD), 500GB | $89.99 | Kingston NV3 on Amazon, via a price tracker [31] |
| DisplayPort-to-HDMI adapter for the screen | $14 | Not confirmed (seller page would not load) |
| Webcam, touchscreen, speakers, LED parts, box, mounts, power strip | $371.30 | Same as tier B |
| **Subtotal** | **$874** | |
| Optional: wake sensor | $3.95 or $14.95 | Not in subtotal; see "Optional extras" |

The Jetson runs warm and may need the vented box ($134.99 [32]).

### Optional extras

- **Wake sensor (any tier).** Wired to the Pico, it wakes the screen and camera when someone comes within about one metre. Option A, distance sensor (VL53L1X): $14.95 at Adafruit [33], $22.95 at Pololu [34]; it can wake at exactly one metre. Option B, motion sensor (HC-SR501): $3.95 at PiShop.us [35], $9.95 at Adafruit [36]; it also wakes for passers-by. It is optional because the camera alone can already detect an item held in view.
- **Bin station, if the site has none.** Three plastic 23-gallon bins with lids: $104.99 (Lavex, WebstaurantStore) [37]. Steel 68-gallon station: $1,439.00 (Busch Systems, WebstaurantStore) [38]. 96-gallon station: $2,189.00 (Busch Systems, Global Industrial) [39].
- **Competitors.** None publishes prices. Oscar Sort (Intuitive AI): reported at $10,000 to $15,000 per installation plus about $5,500 to $6,500 a year [40][41]. Bigbelly: one city paid $3,500 to $4,100 per unit around 2015 to 2017 [42]; Spokane leased its cans for $106,000 a year [43]. EvoBin: no public price found.

## 2. One-time labor

Assumptions: 6 hours per kit (4 to assemble and test, 2 to install) at $30 an hour. 6 hours at $30 is **$180 per kit**; $0 in cash if the team does it. Not counted: the LED control program, which is not written yet.

## 3. Running cost per bin, per month

**AI usage.** Anthropic bills by the "token" (a small chunk of text; photos count too). Prices are from its pricing page [44] and match the team's figures. Estimate per item: 4,800 input tokens, 1,300 cached input tokens (repeated text, billed at a small fraction) and 400 output tokens, averaged over easy items and ones that need a question or a second look. **Based on prompt sizes; not yet measured in a live run.**

| Model | Price per million tokens: input / cached / output | 4,800 input | 1,300 cached | 400 output | Cost per item |
|---|---|---:|---:|---:|---:|
| Claude Haiku 5.5 | $0.10 / $0.01 / $0.50 | 0.048 cents | 0.0013 cents | 0.02 cents | **about 0.07 cents** |
| Claude Sonnet 5.5 | $2 / $0.10 / $10 | 0.96 cents | 0.013 cents | 0.4 cents | **about 1.37 cents** |
| Claude Opus 5.5 | $4 / $0.20 / $20 | 1.92 cents | 0.026 cents | 0.8 cents | **about 2.75 cents** |

For Haiku: 300 items a day at 0.0693 cents each is about 21 cents a day, about $6.24 a month (30 days). The same sum for every case:

| Items a day | Haiku 5.5 a month | Sonnet 5.5 a month | Opus 5.5 a month |
|---|---:|---:|---:|
| 100 | $2.08 | $41.19 | $82.38 |
| 300 | $6.24 | $123.57 | $247.14 |
| 500 | $10.40 | $205.95 | $411.90 |

Cautions: the cached price needs the previous item to be under five minutes earlier; on a quiet bin add up to 0.6 cents per item on Opus, 0.3 on Sonnet, 0.02 on Haiku. The stronger models also "think" before answering, billed as output, so 400 output tokens may be low for Sonnet and Opus.

**Electricity.** A 15-watt device running all day uses 0.36 kilowatt-hours a day, about 10.8 a month. At the US average business price of 14.47 cents per kilowatt-hour (August 2026) [45], that is **about $1.56 a month** ($1.04 at 10 watts; about $2.60 for a 25-watt Jetson, estimate).

**Internet.** Assumption: the site's Wi-Fi, $0. Optional cellular: T-Mobile prepaid data at $10 a month for 2GB, $20 for 5GB or $30 for 10GB, plus taxes and fees [46]. Estimate: a third of a megabyte per item, so 300 items a day is about 3GB a month (the $20 plan). The modem is extra (price not confirmed).

**Maintenance.** Assumption: about 15% of the hardware price a year for failed cards, cables, screens or LEDs; rounded up, **$5 a month** for tier A, **$10** for B, **$11** for C.

## 4. Totals

At 300 items a day per bin on existing Wi-Fi. One-time is parts plus labor, with no bulk discount.

| Setup | One-time | Per month |
|---|---|---|
| One prototype, tier A with Haiku 5.5 | $340 parts + $180 labor = **$520** | $6.24 AI + $1.56 power + $5 upkeep = **about $13** |
| One prototype, tier B with Sonnet 5.5 | $701 parts + $180 labor = **$881** | $123.57 AI + $1.56 power + $10 upkeep = **about $135** |
| Pilot of 10 kits, tier A with Haiku 5.5 | $3,404 parts + $1,800 labor = **about $5,200** | 10 times $12.80 = **about $128** |
| Pilot of 10 kits, tier B with Sonnet 5.5 | $7,013 parts + $1,800 labor = **about $8,810** | 10 times $135.13 = **about $1,350** |

## 5. What drives the cost

The AI model decides the bill. At 300 items a day, Haiku 5.5 costs about $75 a year per bin in AI fees; Sonnet 5.5 costs about $1,480, over four times the whole tier A kit; Opus 5.5, the software's default today, about $2,970. Against that, picking the $700 kit over the $340 kit is a one-time $360. The Jetson has no AI fee, but its power and upkeep alone cost about as much per month as tier A with Haiku costs in total, so it only pays off against Sonnet or Opus, and only if the untested on-device model is accurate enough. **Cheapest sensible setup: tier A on site Wi-Fi with Haiku 5.5** (one setting, SORTY_MODEL): about $340 in parts and $13 a month. Run the 32 test scenarios on Haiku and Sonnet first; move up only if the accuracy gain is worth about $117 more a month per bin.

## Sources

Every source was checked on 2026-11-21.

1. Notebookcheck, Raspberry Pi 2GB price rise of 1 October 2026: https://www.notebookcheck.net/Raspberry-Pi-announces-new-price-hikes-for-2-GB-Pi-4-and-Pi-5.1413412.0.html
2. CNX Software, Jetson price rise of July 2026: https://www.cnx-software.com/2026/07/22/nvidia-increases-the-price-of-jetson-modules-and-devkits-by-up-to-101/
3. CanaKit, Raspberry Pi 5 2GB: https://www.canakit.com/raspberry-pi-5-2gb.html
4. PiShop.us, Raspberry Pi 5 2GB (same price, out of stock, one per customer): https://www.pishop.us/product/raspberry-pi-5-2gb/
5. PiShop.us, Raspberry Pi 27W USB-C power supply: https://www.pishop.us/product/raspberry-pi-27w-usb-c-power-supply-white-us/
6. PiShop.us, SanDisk microSD card with Raspberry Pi OS, 32GB: https://www.pishop.us/product/class-10-microsd-card-with-raspberry-pi-os-bookworm-32gb/
7. CanaKit, Active Cooler: https://www.canakit.com/raspberry-pi-5-active-cooler.html (also PiShop.us, $12.95: https://www.pishop.us/product/raspberry-pi-active-cooler/ and Adafruit, $13.50: https://www.adafruit.com/product/5815)
8. PiShop.us, Camera Module 3: https://www.pishop.us/product/raspberry-pi-camera-module-3/
9. PiShop.us, camera cable for Raspberry Pi 5: https://www.pishop.us/product/camera-cable-for-raspberry-pi-5/
10. PiShop.us, Touch Display 2, 7-inch: https://www.pishop.us/product/raspberry-pi-touch-display-2/
11. CanaKit, Touch Display 2: https://www.canakit.com/raspberry-pi-touch-display-2.html
12. Raspberry Pi, Touch Display 2 list price: https://www.raspberrypi.com/products/touch-display-2/
13. Adafruit, Mini External USB Stereo Speaker: https://www.adafruit.com/product/3369
14. Adafruit, Mini USB Microphone: https://www.adafruit.com/product/3367
15. Adafruit, NeoPixel LED strip, 30 LEDs per metre, 2 m: https://www.adafruit.com/product/2537
16. Adafruit, Raspberry Pi Pico: https://www.adafruit.com/product/4864
17. Adafruit, 74AHCT125 level shifter: https://www.adafruit.com/product/1787
18. Adafruit, 5V 4A power supply: https://www.adafruit.com/product/1466
19. Adafruit small parts: USB cable, $2.95, out of stock: https://www.adafruit.com/product/592 ; jumper wires, $1.95: https://www.adafruit.com/product/1954 ; breadboard, $4.95: https://www.adafruit.com/product/64 ; power jack adapter, $2.00, out of stock: https://www.adafruit.com/product/368 ; plus about $2 for a capacitor and a resistor (estimate)
20. Prusa, Prusament PLA filament, 1 kg: https://www.prusa3d.com/product/prusament-pla-prusa-galaxy-black-1kg/
21. CanaKit, Raspberry Pi 5 4GB: https://www.canakit.com/raspberry-pi-5-4gb.html ; 1GB price: https://www.canakit.com/raspberry-pi-5
22. MeLE store, Quieter 4C SE: https://store.mele.cn/products/mele-quieter-4c-se-grade-fanless-mini-pc-n150
23. Logitech, C920s Pro HD webcam: https://www.logitech.com/en-us/shop/p/c920s-pro-hd-webcam
24. PiShop.us, Waveshare 10.1-inch touch display: https://www.pishop.us/product/10-1inch-capacitive-touch-display-wide-color-gamut-1280-800-optical-bonding-toughened-glass-panel-hdmi-type-c-display-interface/
25. Waveshare, 10.1HP-CAPLCD monitor: https://www.waveshare.com/10.1hp-caplcd-monitor.htm
26. Logitech, S150 USB speakers: https://www.logitech.com/en-us/shop/p/s150-usb-stereo-speakers
27. Altelix, 14x11x5 weatherproof box with hinged door and key lock: https://altelix.com/altelix-14x11x5-pc-abs-weatherproof-utility-box-nema-enclosure-with-hinged-door/
28. Altelix, pole mount kits: https://altelix.com/weatherproof-nema-enclosures/nema-enclosure-accessories/enclosure-pole-mount-wall-mount-kits/?page=2
29. VIVO, pole mount for screens (MOUNT-POLE01): https://vivo-us.com/products/mount-pole01
30. SparkFun, NVIDIA Jetson Orin Nano Super Developer Kit: https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html
31. CheapestSSD price tracker, Amazon US prices: https://cheapestssd.com/
32. Altelix, vented 14x11x5 box: https://altelix.com/altelix-14x11x5-pc-abs-weatherproof-vented-utility-box-nema-enclosure-with-hinged-door/
33. Adafruit, VL53L1X distance sensor: https://www.adafruit.com/product/3967
34. Pololu, VL53L1X distance sensor: https://www.pololu.com/product/3415
35. PiShop.us, HC-SR501 motion sensor: https://www.pishop.us/product/hc-sr501-pyroelectric-infrared-pir-motion-sensor-detector-module/
36. Adafruit, PIR motion sensor: https://www.adafruit.com/product/189
37. WebstaurantStore, Lavex three-stream station kit: https://www.webstaurantstore.com/lavex-23-gallon-3-stream-slim-rectangular-trash-recycle-compost-station-with-black-drop-shot-lid-green-drop-shot-lid-and-blue-can-bottle-lid/475WH23CDSBBKT.html
38. WebstaurantStore, Busch Systems Spectrum, 68 gallon: https://www.webstaurantstore.com/busch-systems-spectrum-101196-68-gallon-steel-three-stream-organics-mobius-loop-waste-receptacle/305101196.html
39. Global Industrial, Busch Systems Mosaic, 96 gallon: https://www.globalindustrial.com/p/mosaic-triple-recycling-station-for-mixed-recyclables-96-gal-cap-blackbluegreen
40. Waste Dive, article of 30 July 2025 quoting Intuitive AI's head of strategy: https://www.wastedive.com/news/ai-recycling-education-oscar-sort-professor-green-los-angeles/756106/
41. The Justice (Brandeis University student paper), article of 16 September 2025, which notes the company does not share its price: https://www.thejustice.org/article/2025/09/brandeis-to-introduce-oscar-sort-recycling-technology-to-campus-brandeis
42. Bigbelly, City of Millbrae, California: https://bigbelly.com/news/bigbelly-compacting-trash-cans-great-for-city-of-millbrae-california-2
43. Yahoo News, article of 11 March 2025 on Spokane's Bigbelly lease: https://www.yahoo.com/news/spokane-replaces-downtown-garbage-cans-020600211.html
44. Anthropic, API pricing: https://platform.claude.com/docs/en/about-claude/pricing
45. US Energy Information Administration, Electric Power Monthly, Table 5.3, data to August 2026, released 23 October 2026: https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_3
46. T-Mobile, prepaid data-only plans: https://prepaid.t-mobile.com/prepaid-internet
