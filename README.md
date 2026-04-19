# UVM Testbench Generator

Generate a **complete, compile-ready UVM 1.2 testbench** from a single YAML config file.

Interfaces · Agents · Driver · Monitor · Coverage · Scoreboard · Virtual Sequences · Makefile · Regression infra — all generated in seconds, in a consistent professional style.

---

## The Problem This Solves

Every new UVM verification project starts with the same 4-6 hours of boilerplate:

- Create `N` interfaces with clocking blocks and modports  
- Create `N` agents, each with item / cfg / sequencer / driver / monitor / cov / pkg  
- Wire them all into an env with config DB, analysis ports, TLM FIFOs  
- Write a scoreboard skeleton, virtual sequencer, test class, top module  
- Set up a makefile with VCS flags, regression loop, coverage commands  

This tool does all of that in **under 5 seconds**.

---

## Quick Start

```bash
# 1. Install dependencies
pip install jinja2 pyyaml

# 2. Generate a TB from config
python3 gen.py config/dut_tb.yaml

# 3. Go straight to writing stimulus
cd generated_dut_tb/sim
make compile
make run VSEQ=smoke_vseq
```

---

## What Gets Generated

For a config with N agents you get this exact directory structure:

```
generated_<project>/
├── interfaces/
│   ├── clk_rst_if.sv               ← clock + reset + apply_reset() task
│   ├── <agent0>_if.sv              ← drv_cb + mon_cb + DRV_MP/MON_MP modports
│   └── <agentN>_if.sv
├── tb_files/
│   ├── pkg/
│   │   └── <project>_chk_pkg.sv   ← checker mode enum (one per vseq)
│   ├── agents/
│   │   └── <agent>_agent/
│   │       ├── <agent>_item.sv     ← rand fields + constraints (TODO: fill in)
│   │       ├── <agent>_agent_cfg.sv
│   │       ├── <agent>_sequencer.sv
│   │       ├── <agent>_driver.sv   ← reset_driver() + drive_transfer() stubs
│   │       ├── <agent>_monitor.sv  ← analysis_port + cov_port
│   │       ├── <agent>_agent_cov.sv ← uvm_subscriber covergroup stub
│   │       ├── <agent>_agent.sv    ← build/connect, UVM_ACTIVE guard
│   │       ├── <agent>_agent_pkg.sv
│   │       └── <agent>_sequences/
│   │           ├── <agent>_st_base_seq.sv
│   │           └── <agent>_st_<name>_seq.sv  ← one per sequence in YAML
│   ├── env/
│   │   ├── env_cfg.sv
│   │   ├── virtual_sequencer.sv    ← one seqr handle per active agent
│   │   ├── scoreboard.sv           ← TLM FIFOs + chk_mode switch
│   │   ├── env.sv                  ← config DB set/get + analysis port wiring
│   │   ├── env_pkg.sv
│   │   └── virtual_sequences/
│   │       ├── base_vseq.sv     ← apply_rst() + get_clk_rst_vif() helpers
│   │       └── st_<name>_vseq.sv   ← fork/join_any + timeout pattern
│   └── tb_test/
│       ├── test_cfg.sv
│       ├── test.sv                 ← +VSEQ= plusarg + factory override
│       └── test_pkg.sv
├── top.sv                          ← DUT instantiation + config DB + fsdb dump
└── sim/
    ├── makefile                    ← compile / run / regress / cov / merge_cov
    └── regress_summary.py          ← colour-coded PASS/FAIL table
```

---

## YAML Config Reference

```yaml
dut_module    : my_dut          # top-level RTL module name
output_dir    : generated_dut_tb # where to write files

clk_period_ns : 10              # clk_rst_if period
reset_cycles  : 5               # initial reset width

global_defines:                 # compiled first (defines, typedefs)
  - design_files/Include/Constant_Defines.sv

design_files:                   # RTL files
  - design_files/my_dut.sv

agents:
  - name      : my_agent        # prefix for all generated files
    active    : true            # UVM_ACTIVE / UVM_PASSIVE
    coverage  : true            # generate cov subscriber
    sequences :                 # one .sv file created per entry
      - smoke
      - burst
      - corner_case
    ports:                      # generates interface signals + clocking blocks
      - { name: valid,  direction: input,  width: 1  }  # TB drives DUT
      - { name: data,   direction: input,  width: 32 }
      - { name: ready,  direction: output, width: 1  }  # DUT drives TB

virtual_seqs:                   # one st_<n>_vseq.sv per entry
  - smoke
  - burst

regression_seqs:                # used in makefile VSEQ_LIST
  - smoke
  - burst

scoreboard  : true
coverage    : true
timeout_ns  : 6000
```

**Port direction convention:**
- `input`  → TB drives this signal into DUT (`output` in drv_cb)
- `output` → DUT drives this signal out (`input` in drv_cb, `input` in mon_cb)

---

## After Generation — What You Fill In

The generator creates correctly wired, compile-ready stubs. You add the protocol-specific logic:

| File | What to add |
|------|-------------|
| `<agent>_item.sv` | `rand` fields matching your protocol, constraints |
| `<agent>_driver.sv` → `drive_transfer()` | Your handshake / burst protocol logic |
| `<agent>_monitor.sv` → `run_phase()` | Transaction boundary detection, item population |
| `<agent>_agent_cov.sv` | Protocol-specific covergroups |
| `scoreboard.sv` → per-agent tasks | Checker logic per `chk_mode` case |
| `virtual_sequences/st_*_vseq.sv` | Instantiate + start your sequences |
| `top.sv` → DUT instantiation | Connect DUT ports to interface signals |

Everything else — packages, includes, TLM connections, config DB, factory override, makefile — is done.

---

## Running the FIFO Demo (Fully Working Example)

The `examples/fifo_tb/` directory contains a **complete end-to-end demo** with a parameterized synchronous FIFO. All drivers, monitors, sequences, scoreboard, and virtual sequences are fully implemented.

```bash
cd examples/fifo_tb
python3 ../../gen.py config/fifo_tb.yaml   # regenerate anytime

cd generated_fifo_tb/sim
make compile
make run VSEQ=smoke_vseq
make run VSEQ=fill_and_drain_vseq
make run VSEQ=simultaneous_wr_rd_vseq SEED=42 DUMP=1
make regress
make cov
```

### FIFO Demo Test Matrix

| Virtual Sequence | What It Tests |
|---|---|
| `smoke_vseq` | Single write + read, basic connectivity |
| `write_then_read_vseq` | 8 writes then 8 reads, data integrity |
| `simultaneous_wr_rd_vseq` | Concurrent wr/rd, fill level stability |
| `fill_and_drain_vseq` | Incremental 0x00–0x0F fill then full drain |
| `overflow_test_vseq` | 20 writes into depth-16 FIFO, backpressure |
| `underflow_test_vseq` | Read from empty FIFO, driver backpressure |
| `reset_mid_op_vseq` | Assert reset mid-burst, verify clean recovery |
| `almost_flags_vseq` | Target almost_full / almost_empty flag assertion |

The scoreboard uses a golden reference queue: every successful write pushes to it, every successful read pops and compares. Data order and value are both checked.

---

## Simulator Compatibility

| Simulator | Status |
|-----------|--------|
| Synopsys VCS + Verdi | Tested |
| Cadence Xcelium | Should work — swap VCS flags in makefile |
| Mentor Questa | Should work — swap VCS flags in makefile |

---

## Project Structure

```
uvm_tb_gen/
├── gen.py                   ← entry point
├── config/
│   └── dut_tb.yaml          ← generic 2-agent starter config
├── templates/               ← Jinja2 templates (edit to change style)
│   ├── interfaces/
│   ├── agent/
│   ├── env/
│   ├── pkg/
│   ├── tb_test/
│   ├── sim/
│   └── top.sv.j2
└── examples/
    └── fifo_tb/             ← fully working FIFO demo
        ├── config/fifo_tb.yaml
        ├── design_files/sync_fifo.sv
        └── generated_fifo_tb/   ← ready to compile and run
```

---

## Extending the Generator

**Add a new template variable** → edit `gen.py::load_config()` defaults  
**Change generated code style** → edit the `.j2` files in `templates/`  
**Add a protocol preset** → create `presets/apb/` with filled-in driver/item templates  
**Support other simulators** → update `templates/sim/makefile.j2`

---

## Requirements

- Python 3.8+
- `pip install jinja2 pyyaml`
- Synopsys VCS + Verdi (or adapt makefile for your simulator)
- UVM 1.2

---

## License

MIT — use freely in personal and commercial projects.

---

## Author

Built from a real production UVM verification environment for a digital IP. The coding style, topology, and patterns in the templates reflect real industry practice.
