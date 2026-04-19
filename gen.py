#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         UVM Testbench Generator — Abdullah's Style                          ║
║  Usage:  python3 gen.py config/my_dut.yaml                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import yaml
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATE_DIR = Path(__file__).parent / "templates"
SCRIPT_DIR   = Path(__file__).parent

def banner(msg):
    w = 70
    print("=" * w)
    print(f"  {msg}")
    print("=" * w)

def info(msg):
    print(f"  [GEN] {msg}")

def render(env_j2, template_name, ctx):
    tpl = env_j2.get_template(template_name)
    return tpl.render(**ctx)

def write(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    info(f"Created  {path}")

# ─────────────────────────────────────────────────────────────────────────────
# Load config
# ─────────────────────────────────────────────────────────────────────────────

def load_config(yaml_path):
    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)

    # ── defaults ──────────────────────────────────────────────────────────────
    cfg.setdefault("project_name",   "my_tb")
    cfg.setdefault("dut_module",     "dut")
    cfg.setdefault("clk_period_ns",  10)
    cfg.setdefault("reset_cycles",   5)
    cfg.setdefault("include_dir",    "design_files/Include")
    cfg.setdefault("global_defines", [])
    cfg.setdefault("design_files",   [])
    cfg.setdefault("scoreboard",     True)
    cfg.setdefault("coverage",       True)
    cfg.setdefault("virtual_seqs",   ["smoke"])
    cfg.setdefault("regression_seqs",["smoke"])
    cfg.setdefault("timeout_ns",     6000)

    for ag in cfg.get("agents", []):
        ag.setdefault("active",   True)
        ag.setdefault("coverage", True)
        ag.setdefault("sequences",["smoke"])
        ag.setdefault("ports",    [])

    return cfg

# ─────────────────────────────────────────────────────────────────────────────
# Main generation
# ─────────────────────────────────────────────────────────────────────────────

def generate(yaml_path):
    cfg      = load_config(yaml_path)
    out_root = Path(cfg.get("output_dir", f"generated_{cfg['project_name']}"))
    env_j2   = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    banner(f"Generating TB for: {cfg['project_name']}")
    info(f"DUT Module : {cfg['dut_module']}")
    info(f"Agents     : {[a['name'] for a in cfg['agents']]}")
    info(f"Output     : {out_root}/")
    print()

    agents = cfg["agents"]

    # ── 1. interfaces/ ────────────────────────────────────────────────────────
    for ag in agents:
        content = render(env_j2, "interfaces/agent_if.sv.j2", {"ag": ag, "cfg": cfg})
        write(out_root / "interfaces" / f"{ag['name']}_if.sv", content)

    clk_rst = render(env_j2, "interfaces/clk_rst_if.sv.j2", {"cfg": cfg})
    write(out_root / "interfaces" / "clk_rst_if.sv", clk_rst)

    # ── 2. per-agent files ────────────────────────────────────────────────────
    for ag in agents:
        a_dir = out_root / "tb_files" / "agents" / f"{ag['name']}_agent"

        for tmpl, fname in [
            ("agent/item.sv.j2",          f"{ag['name']}_item.sv"),
            ("agent/cfg.sv.j2",           f"{ag['name']}_agent_cfg.sv"),
            ("agent/sequencer.sv.j2",     f"{ag['name']}_sequencer.sv"),
            ("agent/driver.sv.j2",        f"{ag['name']}_driver.sv"),
            ("agent/monitor.sv.j2",       f"{ag['name']}_monitor.sv"),
            ("agent/agent.sv.j2",         f"{ag['name']}_agent.sv"),
        ]:
            content = render(env_j2, tmpl, {"ag": ag, "cfg": cfg})
            write(a_dir / fname, content)

        if cfg["coverage"]:
            cov = render(env_j2, "agent/cov.sv.j2", {"ag": ag, "cfg": cfg})
            write(a_dir / f"{ag['name']}_agent_cov.sv", cov)

        # sequences
        seq_dir = a_dir / f"{ag['name']}_sequences"
        base_seq = render(env_j2, "agent/sequences/base_seq.sv.j2", {"ag": ag, "cfg": cfg})
        write(seq_dir / f"{ag['name']}_base_seq.sv", base_seq)

        for seq in ag["sequences"]:
            s = render(env_j2, "agent/sequences/seq.sv.j2",
                       {"ag": ag, "seq_name": seq, "cfg": cfg})
            write(seq_dir / f"{ag['name']}_{seq}_seq.sv", s)

        # package
        pkg = render(env_j2, "agent/pkg.sv.j2", {"ag": ag, "cfg": cfg})
        write(a_dir / f"{ag['name']}_agent_pkg.sv", pkg)

    # ── 3. env/ ───────────────────────────────────────────────────────────────
    env_dir = out_root / "tb_files" / "env"

    for tmpl, fname in [
        ("env/env_cfg.sv.j2",         "env_cfg.sv"),
        ("env/virtual_sequencer.sv.j2","virtual_sequencer.sv"),
        ("env/scoreboard.sv.j2",      "scoreboard.sv"),
        ("env/env.sv.j2",             "env.sv"),
        ("env/env_pkg.sv.j2",         "env_pkg.sv"),
    ]:
        content = render(env_j2, tmpl, {"agents": agents, "cfg": cfg})
        write(env_dir / fname, content)

    # virtual sequences
    vseq_dir = env_dir / "virtual_sequences"
    base_vs = render(env_j2, "env/virtual_sequences/base_vseq.sv.j2",
                     {"agents": agents, "cfg": cfg})
    write(vseq_dir / "base_vseq.sv", base_vs)

    for vs in cfg["virtual_seqs"]:
        content = render(env_j2, "env/virtual_sequences/vseq.sv.j2",
                         {"agents": agents, "cfg": cfg, "vseq_name": vs})
        write(vseq_dir / f"{vs}_vseq.sv", content)

    # ── 4. pkg/ ───────────────────────────────────────────────────────────────
    chk_pkg = render(env_j2, "pkg/chk_pkg.sv.j2", {"cfg": cfg})
    write(out_root / "tb_files" / "pkg" / f"{cfg['project_name']}_chk_pkg.sv", chk_pkg)

    # ── 5. tb_test/ ───────────────────────────────────────────────────────────
    test_dir = out_root / "tb_files" / "tb_test"
    for tmpl, fname in [
        ("tb_test/test_cfg.sv.j2", "test_cfg.sv"),
        ("tb_test/test.sv.j2",     "test.sv"),
        ("tb_test/test_pkg.sv.j2", "test_pkg.sv"),
    ]:
        content = render(env_j2, tmpl, {"agents": agents, "cfg": cfg})
        write(test_dir / fname, content)

    # ── 6. top.sv ─────────────────────────────────────────────────────────────
    top = render(env_j2, "top.sv.j2", {"agents": agents, "cfg": cfg})
    write(out_root / "top.sv", top)

    # ── 7. sim/makefile ───────────────────────────────────────────────────────
    makefile = render(env_j2, "sim/makefile.j2", {"agents": agents, "cfg": cfg})
    write(out_root / "sim" / "makefile", makefile)

    regress = render(env_j2, "sim/regress_summary.py.j2", {"cfg": cfg})
    write(out_root / "sim" / "regress_summary.py", regress)

    # ── 8. design_files/ — only create dirs referenced in YAML ───────────────
    # Collect every unique directory mentioned in global_defines + design_files
    all_rtl = cfg.get("global_defines", []) + cfg.get("design_files", [])
    rtl_dirs = set()
    for entry in all_rtl:
        rtl_dirs.add((out_root / Path(entry)).parent)

    # Also always create the top-level design_files/ so the user has somewhere
    # to drop RTL, but nothing more
    rtl_dirs.add(out_root / "design_files")

    for d in sorted(rtl_dirs):
        d.mkdir(parents=True, exist_ok=True)
        info(f"Created  {d}/")

    print()
    banner("Generation complete!")
    print(f"\n  Output directory : {out_root}/")
    print(f"  Agents generated : {len(agents)}")
    print()
    print("  Next steps:")
    print("    1. Copy your design RTL into design_files/")
    print("    2. Fill in interface signals in interfaces/*_if.sv")
    print("    3. Add driver/monitor logic in *_driver.sv / *_monitor.sv")
    print("    4. Add scoreboard checks in env/scoreboard.sv")
    print("    5. Run:  cd sim && make compile")
    print()

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 gen.py <config.yaml>")
        sys.exit(1)
    generate(sys.argv[1])
