-- Bootstrap for the e2e sandbox Postgres (docker compose --profile sandbox).
--
-- Only the pieces the application cannot create for itself belong here. The app
-- and ledger schemas are `CREATE TABLE IF NOT EXISTS` statements run on first
-- connect, so they need no help; the `vector` extension does, because creating
-- an extension needs privileges the pooled application role uses at connect
-- time rather than at migration time.
CREATE EXTENSION IF NOT EXISTS vector;
