# canonical-substrate (portable bundle)

A dependency-free, drop-in export of the MIZ OKI canonical event contract:
**JourneyEvent v1 → CanonicalEventEnvelope v2 → cross-event identity clusters**, all
computed deterministically at the SENSE stage.

This directory is a **port kit**, not a maintained second copy. It exists so the
contract can be lifted into the production agent runtime (`boss-agent-adk` /
MIZOKICloudRun) as the single source of truth. See **[PORTING.md](./PORTING.md)** for
the wire-in.

```bash
cd portable/canonical-substrate
python3 -m unittest tests.test_substrate     # 3 tests, OK — proves it runs with no Flask/runtime
```

```python
from canonical_substrate import normalizer, envelope_builder, IdentityResolutionCell

event = normalizer().normalize("meta", payload)          # v1 JourneyEvent
built = envelope_builder().build_and_validate(event)     # v2 envelope (+ valid/errors)
cluster = IdentityResolutionCell("clusters.json").resolve_actor(event["actor"])
built["envelope"]["identity"]["identity_cluster"] = cluster["identity_cluster"]
```

Source of record (until the port lands): `mizoki_runtime/` in `mizoki-3-5-website`.
