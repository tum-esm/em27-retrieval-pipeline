Log files are names according to the schema `YYYYMMDD-HH-MM.log`. `YYYYMMDD` is the date, `HH-MM` is the time.

You can make a cron job write its outputs in a file names like this:

```bash
proffast_error_file = ".../logs/cron/$(date '+%Y%m%d-%H-%M').log"
0 0,3,6,9,12,15,18,21 * * * .../.venv/bin/python .../main.py > ${proffast_error_file}
```
