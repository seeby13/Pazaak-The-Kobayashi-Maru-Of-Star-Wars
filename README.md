# Pazaak: The Kobayashi Maru of Star Wars

*An unnecessarily thorough statistical investigation into whether Pazaak cheats.*

📄 **Paper:** `docs/Pazaak_The_Kobayashi_Maru_Of_Star_Wars.pdf`
💻 Source Code: Browse Repository
👤 Author: Sebastian Böker

---

## Overview

This project investigates one of the oldest accusations in gaming:

> Pazaak is rigged.

After suffering an unreasonable number of losses against Suvam Tan on Yavin Station, I decided to stop complaining and start collecting evidence.

The project combines:

* Monte Carlo simulation
* Dynamic programming
* Statistical hypothesis testing
* Computer vision
* Template matching
* Video-based gameplay extraction

to determine whether *Star Wars: Knights of the Old Republic* manipulates Pazaak card draws in favour of NPC opponents.

The short version:

> No convincing evidence of manipulated card draws was found.
>
> The game is still unfair.
>
> Just not for the reason I wanted.

---

## Project Components

The repository consists of two major parts.

### 1. Pazaak Simulation

A simplified implementation of Pazaak used to establish a theoretical baseline.

Features include:

* Infinite uniform deck
* Threshold-based strategies
* Probability-based strategies
* Recursive dynamic-programming strategy
* Monte Carlo evaluation

The simulator was primarily used to investigate the structural advantage of acting second.

### 2. Gameplay Extraction Pipeline

A computer-vision pipeline used to analyze real gameplay recordings.

Workflow:

```text
Gameplay Video
        ↓
Board State Extraction
        ↓
Draw Event Reconstruction
        ↓
Statistical Analysis
```

This allows card draws to be reconstructed directly from recorded gameplay without access to the game source code.

---

## Repository Structure

```text
.
├── docs/
│   └── Pazaak_The_Kobayashi_Maru_Of_Star_Wars.pdf
│
├── data/
│   ├── extracted/
│   └── debug/
│
├── templates/
├── screenshots/
├── game_recordings/
│
├── simulate_pazaak.py
├── player.py
├── result.py
├── stats.py
├── slot_grid.py
│
├── extract_pazaak_video.py
├── extract_draw_events.py
│
├── analyze_draw_events.py
├── analyze_sequences.py
├── simulate_sequence_baseline.py
│
├── click_coords.py
├── test_template_matching.py
├── debug_slots.py
├── debug_top3_matches.py
├── debug_draw_events.py
├── debug_rounds.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Typical Workflow

### 1. Record Gameplay

Store gameplay recordings in:

```text
game_recordings/
```

### 2. Extract Board States

```bash
python extract_pazaak_video.py
```

Produces:

```text
data/extracted/pazaak_state_changes.csv
```

### 3. Reconstruct Draw Events

```bash
python extract_draw_events.py
```

Produces:

```text
data/extracted/pazaak_draw_events.csv
```

### 4. Analyze Card Frequencies

```bash
python analyze_draw_events.py
```

### 5. Analyze Draw Sequences

```bash
python analyze_sequences.py
```

### Optional Validation

```bash
python debug_slots.py
python debug_draw_events.py
python debug_rounds.py
python debug_top3_matches.py
```

---

## Results Summary

The analyzed recordings showed card distributions highly consistent with a fair uniform deck.

Chi-square tests found no statistically significant deviations from the expected card frequencies.

Several sequence-based analyses initially appeared suspicious. However, these effects disappeared after restricting the analysis to directly observed events and validating the reconstruction pipeline.

No convincing evidence of manipulated card draws was found in the analyzed recordings.

The most likely explanation for the perceived unfairness of Pazaak is the structural advantage of acting second.

---

## Report

A full write-up of the investigation is included in:

```text
docs/Pazaak_The_Kobayashi_Maru_Of_Star_Wars.pdf
```

The report documents:

* simulation methodology
* extraction pipeline design
* statistical analyses
* validation procedures
* final conclusions

---

## Future Work

Possible extensions include:

* Side-deck modelling
* NPC decision analysis
* Save-state RNG investigation
* Additional gameplay recordings
* Analysis of other Pazaak opponents

---

## Acknowledgements

Special thanks to:

* Suvam Tan
* HK-47
* The Gizka on Yavin Station, sole witness to a significant portion of this investigation

No merchants were harmed during this investigation.

Several save files, however, suffered repeated and irreversible trauma.
