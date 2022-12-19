# Retrieval State Report

## Brief description
The script generates CSV and markdown reports for available interferograms in the upload and archive directories.
The sript creates two types of results: a summary and a station based report. The summary includes both directories.
```python
SummaryDataGenerator(config, "summary", "csv").generate_report()
StationDataGenerator(config, "version", "md").generate_report()
```
If md is set, multiple svg images would be generated and a single md file that includes all of the images.
In case of csv reports, a separate csv is created for each retrieval version, or a single summary.
## Settings
The settings are sotred in a json file. The ifg_pattern field is a regexp.
```json
{
  "archive_dir_location": "data/archive",
  "upload_dir_location": "data/upload_dir",
  "reports_output": "reports",
  "ifg_pattern": "m?????????.ifg.????"
}
```


