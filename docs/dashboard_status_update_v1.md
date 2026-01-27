# Brady Crime Gun Dashboard: Status Update

**For the Pro Bono Team**

---

## What the Dashboard Shows (v1)

The dashboard is live with 635 crime gun events from Delaware's Gunstat program. You can:

- **See key metrics** — total crime guns, unique dealers, unique manufacturers, interstate trafficking percentage
- **Review dealer risk rankings** — FFLs ranked by a composite score (crime gun count, interstate trafficking, DL2 program status, revoked/charged status), color-coded by risk level
- **Analyze manufacturers** — which companies' guns are ending up in Delaware crimes
- **Track trafficking flows** — where Delaware's crime guns are coming from
- **Export data** — download filtered records as CSV, with full traceability back to source spreadsheets

---

## New: Crime Location Columns

The data we receive doesn't always clearly state where crimes occurred. To fix this, we're computing six standardized fields for every record:

| Column | Description |
|--------|-------------|
| crime_location_state | State where crime/recovery occurred |
| crime_location_city | City |
| crime_location_zip | ZIP code when available |
| crime_location_court | Court jurisdiction (for federal cases) |
| crime_location_pd | Police department involved |
| crime_location_reasoning | How we determined the location (audit trail) |

These columns become the unifying key that lets us combine data across sources. Once populated, you can ask "show me every dealer linked to crimes in Philadelphia" and get results from all our datasets, not just one spreadsheet.

---

## Next Steps (v2)

We're adding the Crime Gun Dealer Database (~2,000 federal court cases) to the pipeline. This adds prosecutorial context: case names, trafficking patterns, detailed narratives.

We'll extract jurisdiction from multiple signals (explicit recovery locations, court references like "E.D. Pa.", trafficking flows like "AK→CA", and narrative text), with confidence levels so you know which extractions to trust.

The goal: select any jurisdiction and immediately see every dealer and manufacturer linked to crime guns there, with risk scores and case documentation.

---

*January 2026*
