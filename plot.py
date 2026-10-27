"""Create docs/*.png from the simulation data (needs matplotlib)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from snm import interp, load, snm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUILD, DOCS = ROOT / "build", ROOT / "docs"
DOCS.mkdir(exist_ok=True)


def transient():
    rows = [[float(v) for v in line.split()] for line in (BUILD / "sram_tran.dat").read_text().splitlines()]
    t = [r[0] * 1e9 for r in rows]
    names = ["WL", "Q", "QB", "BL", "BLB"]
    fig, axes = plt.subplots(len(names), 1, figsize=(8, 7), sharex=True)
    for i, (ax, name) in enumerate(zip(axes, names)):
        ax.plot(t, [r[2 * i + 1] for r in rows], lw=1.4)
        ax.set_ylabel(f"{name} (V)")
        ax.set_ylim(-0.1, 2.0)
        ax.grid(alpha=0.3)
    for ax, (x0, x1, label) in zip([axes[0]] * 2, [(2, 12, "write 1"), (25, 45, "read")]):
        ax.axvspan(x0, x1, color="tab:orange", alpha=0.15)
        ax.text((x0 + x1) / 2, 1.5, label, ha="center", fontsize=9)
    axes[-1].set_xlabel("time (ns)")
    fig.suptitle("6T SRAM: write a 1, precharge, read it back")
    fig.tight_layout()
    fig.savefig(DOCS / "transient.png", dpi=130)
    plt.close(fig)


def butterfly():
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.4))
    for ax, kind in zip(axes, ["hold", "read"]):
        vin, vout = load(BUILD / f"vtc_{kind}.dat")
        ax.plot(vin, vout, label="inverter 1")
        ax.plot(vout, vin, label="inverter 2 (mirror)")
        ax.set_title(f"{kind.capitalize()} butterfly, SNM = {snm(vin, vout) * 1000:.0f} mV")
        ax.set_xlabel("Q (V)")
        ax.set_ylabel("QB (V)")
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "butterfly.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    transient()
    butterfly()
    print("wrote docs/transient.png and docs/butterfly.png")
