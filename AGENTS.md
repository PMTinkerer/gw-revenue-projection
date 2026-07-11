# gw-revenue-projection

May-Oct revenue projection tool: stdlib CLI plus a single-file HTML report with Canva-sized PNG chart export.

## Workspace Atlas

This repo is one of ~30 projects in Lucas Knowles's SCMaine workspace. The
workspace atlas — `~/atlas` locally, https://github.com/PMTinkerer/atlas —
is the source of truth for what exists, where features live, and the
cross-project rules. Consult it before building anything that might already
exist elsewhere.

- Cold start: `~/atlas/ATLAS.md`
- This project's card: `~/atlas/projects/gw-revenue-projection.md`
- "Where does X already live": `~/atlas/capabilities.md`
- External-service patterns: `~/atlas/integrations.md`

Rules that matter most in this repo:

- Pin every dependency exactly; SHA-pin GitHub Actions; no emojis anywhere; secrets never in code (~/.env or project .env).

After shipping a change here, update the project's card and its
`last_verified` date in the atlas (see `~/atlas/protocol/UPDATE.md`).
