# sram-6t-bitcell

[![Simulate](https://github.com/YOUR-USERNAME/sram-6t-bitcell/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/sram-6t-bitcell/actions)

A **6-transistor SRAM bitcell** simulated in [ngspice](https://ngspice.sourceforge.io/).
It writes a bit, precharges the bitlines, reads the bit back, and measures how stable
the cell is. Everything runs from one command and is checked automatically.

![Write and read waveforms](docs/transient.png)

## What is measured

| Measurement | Result (default cell) | How |
|---|---|---|
| Write a 1 | Q = 1.80 V, QB = 0 V | Transient: drive BL/BLB while the word line is high |
| Read access time | **108 ps** to a 100 mV bitline split | Transient: word line rise to `V(BL) - V(BLB) = 100 mV`, 200 fF bitlines |
| Read disturb | QB bumps to **266 mV**, cell keeps its value | Transient: peak of the stored-0 node during a read |
| Hold SNM | **631 mV** | Butterfly curve, word line off |
| Read SNM | **297 mV** | Butterfly curve, word line on, bitlines at VDD |

![Butterfly curves](docs/butterfly.png)

### Read stability vs. cell ratio

The cell ratio is pull-down width divided by access-transistor width. A larger ratio
makes the stored 0 harder to disturb during a read, so read SNM rises:

| Cell ratio | Hold SNM | Read SNM |
|---:|---:|---:|
| 1.00 | 648 mV | 247 mV |
| 1.29 | 641 mV | 268 mV |
| 1.79 (default) | 631 mV | 297 mV |
| 2.50 | 619 mV | 327 mV |
| 3.57 | 605 mV | 358 mV |

## Run it

Requirements: `ngspice` and Python 3 (`sudo apt install ngspice`). Plots also need `matplotlib`.

```bash
make test     # simulate everything and check the results
make plots    # regenerate docs/*.png
```

`make test` fails if a write does not succeed, the read is too slow, a read flips the
cell, or read SNM does not improve with cell ratio.

## How it works

- `spice/sram_6t_transient.cir`: the cell (two inverters plus two access NMOS), bitline
  capacitance, write drivers, precharge switches and a word-line pulse sequence.
- `spice/sram_6t_snm.cir`: one half-cell voltage transfer curve with and without the
  access transistor on. The cell is symmetric, so the second butterfly curve is the mirror image.
- `scripts/snm.py`: finds the largest square that fits inside the smaller eye of the
  butterfly plot. That square's side is the static noise margin.
- `scripts/check.py`: runs ngspice, parses the results, runs the cell-ratio sweep and
  prints PASS/FAIL for each check.
- `spice/models/generic_180nm.lib`: transistor models.

Cell sizing (L = 0.18 µm everywhere): pull-down 0.50 µm, access 0.28 µm, pull-up 0.28 µm, VDD = 1.8 V.

## Limitations

- The transistor models are generic **SPICE Level 1** textbook values, not a foundry
  process, so absolute numbers are illustrative. Replace `generic_180nm.lib` with a real
  PDK or BSIM model to get realistic results.
- The SNM cell is perfectly symmetric (no device mismatch or Monte Carlo).
- The very first picoseconds of the transient show a small startup glitch caused by the
  `uic` initial conditions. It settles long before the write begins.
- Write ability is shown by a successful write, not by a write-margin sweep.

## Ideas to extend

Write margin sweep, Monte Carlo mismatch on SNM, temperature and VDD corners, a sense
amplifier, or a 2x2 array.

## License

MIT
