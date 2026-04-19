# FIFO TB — Complete Working Demo

This is a **fully implemented** UVM 1.2 testbench for a parameterized synchronous FIFO.
Every file is filled in — no stubs. Clone, compile, and run immediately.

## DUT

`design_files/sync_fifo.sv` — Parameterized synchronous FIFO
- DATA_WIDTH = 8, DEPTH = 16 (set in top.sv, easily changed)
- Write port: `wr_en`, `wr_data`, `full`, `almost_full`
- Read port: `rd_en`, `rd_data`, `empty`, `almost_empty`
- Status: `fill_level`

## Quick Start

```bash
# Step 1: Generate (or skip — generated_fifo_tb/ is already included)
python3 ../../gen.py config/fifo_tb.yaml

# Step 2: Compile
cd generated_fifo_tb/sim
make compile

# Step 3: Run a test
make run VSEQ=smoke_vseq
make run VSEQ=fill_and_drain_vseq
make run VSEQ=simultaneous_wr_rd_vseq SEED=42 DUMP=1

# Step 4: Full regression (8 tests × 3 seeds = 24 simulations)
make regress

# Step 5: Coverage
make cov
```

## Test Scenarios

| VSEQ | Scenario |
|------|----------|
| `smoke_vseq` | 1 write + 1 read |
| `write_then_read_vseq` | 8 writes, then 8 reads |
| `simultaneous_wr_rd_vseq` | Concurrent write + read threads |
| `fill_and_drain_vseq` | Fill with 0x00–0x0F, drain all |
| `overflow_test_vseq` | 20 writes into depth-16 FIFO |
| `underflow_test_vseq` | Read from empty, then fill and read |
| `reset_mid_op_vseq` | Reset mid-burst, verify clean recovery |
| `almost_flags_vseq` | Exercise almost_full / almost_empty flags |

## Scoreboard

Golden reference queue mirrors DUT:
- Every successful write (`wr_en && !full`) pushes to `ref_q`
- Every successful read (`rd_en && !empty`) pops from `ref_q` and compares `rd_data`
- Final report shows PASS/FAIL count + overflow/underflow events

## Coverage

Two covergroups:
- `wr_cg`: data value range bins, fill level at write time, full/almost_full toggle
- `rd_cg`: data value range bins, fill level at read time, empty/almost_empty toggle
- Cross coverage: data value × fill level for both agents
