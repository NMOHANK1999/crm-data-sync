# CRM Sync (Backend Track)

This is a **practice mock**, built to mirror the shape of the Rox FDE
backend takehome (Python / FastAPI / SQLite, legacy CRM → platform sync,
five graduated levels). It is not the real assessment and won't match it
exactly — the actual scenario stays hidden until your slot. Use this to
rehearse the *mechanics*: reading a partially-built service cold, working
under a strict clock, and making judgment calls on messy data.

## Setup

```bash
cd fde-mock-takehome
python3 -m venv .venv && source .venv/bin/activate   # or use uv if you prefer
pip install -r requirements.txt
python doctor.py
```

Do this once, well before you start the timer.

## Running it

Two services, two terminals:

```bash
# terminal 1
uvicorn mock_crm.main:app --port 8001 --reload

# terminal 2
uvicorn platform_service.main:app --port 8000 --reload
```

Then, e.g.:

```bash
curl -X POST http://localhost:8000/sync
curl http://localhost:8000/customers
curl http://localhost:8000/quarantine
```

Or just run the test suite directly — it spins up the mock CRM itself:

```bash
pytest tests/ -v
```

Run a single level while you work: `pytest tests/test_level1_basic_sync.py -v`

## The task

Implement the TODOs in `platform_service/sync.py`, in order:

1. **`normalize_contact`** — map the CRM's messy, drifting schema onto a
   consistent shape (`tests/test_level1_basic_sync.py`).
2. Extend `normalize_contact` (and quarantine routing in `run_sync`) to
   handle genuinely broken records without crashing the batch
   (`tests/test_level2_messy_data.py`).
3. **`upsert_customer`** — idempotent insert/update keyed on crm_id
   (`tests/test_level3_idempotent_upsert.py`).
4. **`find_existing_customer`** (wire it into `upsert_customer`) —
   cross-crm_id dedup by matching person, plus stale-write protection
   (`tests/test_level4_dedup_conflict.py`).
5. Open-ended — soft deletes, incremental sync, better reporting, whatever
   you think is worth 10-15 remaining minutes
   (`tests/test_level5_open_ended.py`).

Read `platform_service/sync.py`'s docstrings before writing anything —
they describe exactly what each level expects, and the tests are the
actual spec, not this README.

## Suggested timebox (60 min)

- 5 min: read `mock_crm/seed_data.py`, `platform_service/sync.py`, and all
  five test files. Know what's coming before you write code.
- 20 min: level 1
- 15 min: level 2
- 15 min: level 3
- remaining: level 4, then level 5 if there's time. Don't start level 4
  with less than 10 minutes left — a half-done level 4 that breaks level 3
  is worse than a solid stop at level 3.

The real exercise is intentionally too big to finish. Two levels done
thoroughly beats five done superficially — same rule applies here.

## Before you start, for real

- Set a visible 60-minute timer. Don't peek at "just a bit more."
- Keep `DECISIONS_TEMPLATE.md` open and jot notes as you go — where you
  used AI, what you rejected and why, tradeoffs you made under time
  pressure. Reconstructing this afterward from memory is worse than
  writing one line each time it happens.
- Talk yourself through your choices out loud as if narrating to an
  interviewer, even alone. The real format ends in a walkthrough where you
  defend what you shipped — practicing that muscle matters as much as the
  code.
