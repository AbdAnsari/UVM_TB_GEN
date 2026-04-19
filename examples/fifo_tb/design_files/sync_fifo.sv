//============================================================
// Module  : sync_fifo
// Description : Synchronous FIFO with full/empty flags
//               Parameterized depth and data width
//============================================================

module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH      = 16,
    parameter ADDR_WIDTH = $clog2(DEPTH)
)(
    input  logic                  clk,
    input  logic                  rst_n,

    // Write port
    input  logic                  wr_en,
    input  logic [DATA_WIDTH-1:0] wr_data,
    output logic                  full,
    output logic                  almost_full,    // 1 slot left

    // Read port
    input  logic                  rd_en,
    output logic [DATA_WIDTH-1:0] rd_data,
    output logic                  empty,
    output logic                  almost_empty,   // 1 entry left

    // Status
    output logic [ADDR_WIDTH:0]   fill_level      // 0..DEPTH
);

    // ── Storage ───────────────────────────────────────────
    logic [DATA_WIDTH-1:0] mem [DEPTH];

    // ── Pointers ──────────────────────────────────────────
    logic [ADDR_WIDTH:0] wr_ptr;   // extra bit for full/empty
    logic [ADDR_WIDTH:0] rd_ptr;

    // ── Derived ───────────────────────────────────────────
    assign fill_level   = wr_ptr - rd_ptr;
    assign full         = (fill_level == DEPTH);
    assign empty        = (fill_level == 0);
    assign almost_full  = (fill_level == DEPTH - 1);
    assign almost_empty = (fill_level == 1);

    // ── Write ─────────────────────────────────────────────
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= '0;
        end else if (wr_en && !full) begin
            mem[wr_ptr[ADDR_WIDTH-1:0]] <= wr_data;
            wr_ptr                      <= wr_ptr + 1;
        end
    end

    // ── Read ──────────────────────────────────────────────
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr  <= '0;
            rd_data <= '0;
        end else if (rd_en && !empty) begin
            rd_data <= mem[rd_ptr[ADDR_WIDTH-1:0]];
            rd_ptr  <= rd_ptr + 1;
        end
    end

endmodule
