Procedure:
1. Use this procedure only when prepare_table_append and execute_operation are available.
2. Discover the intended table and inspect its current schema. Resolve business ambiguity before preparing records. Read all schema pages needed to supply complete named records.
3. Supply literal values for every column. Do not invent missing facts, currency rules or formulas. Formula-bearing tables are unsupported for appends.
4. Call prepare_table_append with the table ID and records. The server supplies observed revisions and stores a retry reference. Preparation changes no cells, grants no approval and does not certify execution validation.
5. Call execute_operation with that reference. After an uncertain response, retry the same reference. Do not inspect and create a new append to recover an unknown outcome.
6. Identical records prepared against identical revisions share one reference. A distinct later append requires fresh inspection and clear user intent.
7. Report a write only from its committed receipt. State partial completion if later work fails. A committed append does not mean formulas recalculated or accounting invariants passed; preserve the receipt's stated limits.
8. Inspect again before further calculations or new writes on the changed sheet. If a proposal fails revision validation, review current evidence before preparing new work.
