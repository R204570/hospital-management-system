# Setup & Maintenance Scripts

One-off data-seeding and maintenance utilities for the Hospital Management
System. They are **standalone scripts** (not Django management commands) that
bootstrap Django themselves.

## Running

Run any script **from the project root** with the project's virtualenv:

```bash
python setup/<script_name>.py
```

Each script inserts the project root onto `sys.path`, so it works from the
`setup/` folder without extra configuration. Run these **after** migrations
(`python manage.py migrate`).

## Scripts

| Script | Purpose |
|--------|---------|
| `data_import.py` | Main data seeder - populates patients, staff, medicines, suppliers, and related demo data. Run this first. |
| `pharmacy_manufacturers.py` | Seeds / updates medicine manufacturer information. |
| `update_medicine_dosages.py` | Fills in / normalizes medicine dosage strengths and forms. |
| `update_suppliers.py` | Seeds / updates pharmacy supplier records. |
| `standardize_medicine_quantities.py` | Normalizes medicine stock quantities to a consistent format (interactive). |
| `auto_standardize_medicine_quantities.py` | Non-interactive version of the above (safe to schedule). |
| `prune_duplicate_medicines.py` | Finds and removes duplicate medicine records (interactive). |
| `auto_prune_duplicate_medicines.py` | Non-interactive version of the above. |
| `auto_check_emails.py` | Polls the mailbox for inbound email replies (wraps the `check_email_replies` management command). Intended to be scheduled every 5-10 min. Writes `email_check.log` in the working directory. |

## Notes

- The `auto_*` variants are meant for automation/cron; the plain versions may
  prompt for confirmation.
- Email checking requires the `.env` mail credentials to be configured
  (see the main README).
