"""Run the SRAM simulations, print a results table and fail on bad behaviour."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from snm import load, snm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
WPD_SWEEP = [0.28, 0.36, 0.50, 0.70, 1.00]   # pull-down widths in um (access = 0.28 um)
ACCESS_W = 0.28


def ngspice(netlist: Path, log: Path):
    subprocess.run(["ngspice", "-b", "-o", str(log), str(netlist)], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def parse_log(log: Path):
    vals = {}
    for line in log.read_text().splitlines():
        m = re.match(r"^(\w+)\s+=\s+([-+0-9.eE]+)", line)
        if m:
            vals[m.group(1)] = float(m.group(2))
    return vals


def vtc_snm(path: Path):
    vin, vout = load(path)
    return snm(vin, vout)


def sweep_point(wpd_um: float):
    text = (ROOT / "spice" / "sram_6t_snm.cir").read_text()
    text = text.replace(".param wpd=0.5u", f".param wpd={wpd_um}u")
    tag = f"w{int(round(wpd_um * 100)):03d}"
    text = text.replace("build/vtc_", f"build/sweep_{tag}_")
    net = BUILD / f"sweep_{tag}.cir"
    net.write_text(text)
    ngspice(net, BUILD / f"sweep_{tag}.log")
    return vtc_snm(BUILD / f"sweep_{tag}_hold.dat"), vtc_snm(BUILD / f"sweep_{tag}_read.dat")


def main():
    BUILD.mkdir(exist_ok=True)
    failures = []

    def check(name, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            failures.append(name)

    print("Transient: write 1, precharge, read")
    ngspice(ROOT / "spice" / "sram_6t_transient.cir", BUILD / "sram_tran.log")
    m = parse_log(BUILD / "sram_tran.log")
    check("write succeeds", m["q_after_write"] > 1.7 and m["qb_after_write"] < 0.1,
          f"Q={m['q_after_write']:.2f} V, QB={m['qb_after_write'] * 1000:.1f} mV")
    check("read access time < 1 ns", m["t_read_access"] < 1e-9,
          f"{m['t_read_access'] * 1e12:.0f} ps to a 100 mV bitline split")
    check("read does not flip the cell", m["qb_read_peak"] < 0.5 and m["q_after_read"] > 1.7,
          f"QB bump peaks at {m['qb_read_peak'] * 1000:.0f} mV, Q after read = {m['q_after_read']:.2f} V")

    print("\nStatic noise margin (default cell, pull-down 0.50 um, access 0.28 um)")
    ngspice(ROOT / "spice" / "sram_6t_snm.cir", BUILD / "sram_snm.log")
    hold, read = vtc_snm(BUILD / "vtc_hold.dat"), vtc_snm(BUILD / "vtc_read.dat")
    check("hold SNM > read SNM", hold > read, f"hold = {hold * 1000:.0f} mV, read = {read * 1000:.0f} mV")
    check("read SNM positive (cell is read-stable)", read > 0.1, f"{read * 1000:.0f} mV")

    print("\nRead SNM vs cell ratio (pull-down width / access width)")
    print("  cell ratio | hold SNM | read SNM")
    reads = []
    for w in WPD_SWEEP:
        h, r = sweep_point(w)
        reads.append(r)
        print(f"  {w / ACCESS_W:10.2f} | {h * 1000:5.0f} mV | {r * 1000:5.0f} mV")
    check("read SNM grows with cell ratio", all(a < b for a, b in zip(reads, reads[1:])),
          " < ".join(f"{r * 1000:.0f}" for r in reads) + " mV")

    print("\nOverall:", "FAILED" if failures else "ALL CHECKS PASSED")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
