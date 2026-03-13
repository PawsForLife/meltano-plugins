# partition-path-extraction-date-clarity

## The request

Partition path resolution in target-gcs has two valid intents: (1) schema-driven path from `x-partition-fields` and record, and (2) when `x-partition-fields` is missing or empty, the path is the extraction date (e.g. run date). The second is not a "fallback" for failure—it is the intended behaviour when no partition fields are specified. The request was to rename and reword so code and docs use "extraction date" instead of "fallback" for that case, with no behaviour change.

## Planned approach

- **API:** `fallback_date` → `extraction_date` in `get_partition_path_from_schema_and_record`; docstring updated to describe extraction date when x-partition-fields is missing or empty.
- **Sink:** `self.fallback` → `self._extraction_date`; all "fallback" wording in partition-path context → "extraction date" in comments and docstrings; call site updated to pass `extraction_date=self._extraction_date`.
- **Tests:** Constants `FALLBACK_DATE` → `EXTRACTION_DATE` in test_partition_path.py and test_partition_key_generation.py; test names and docstrings updated (e.g. `uses_fallback` → `uses_extraction_date`, `key_contains_fallback_date` → `key_contains_extraction_date`); local `fallback_path` → `extraction_date_path` where applicable.
- **Docs:** AI context (signature, GCSSink, Hive partitioning) and target-gcs CHANGELOG updated to use extraction date and the new parameter name. Implementation order: partition_path.py → sinks.py → tests → documentation.

## What was implemented

- **partition_path.py:** Parameter `fallback_date` → `extraction_date`; docstring now states "extraction date" when x-partition-fields is missing or empty (e.g. run/extraction date).
- **sinks.py:** Attribute `self.fallback` → `self._extraction_date`; comment and class/process_record docstrings use "extraction date"; call to helper uses `extraction_date=self._extraction_date`.
- **Tests:** In test_partition_path.py: `EXTRACTION_DATE`, `extraction_date=EXTRACTION_DATE`, and test renames `uses_fallback` → `uses_extraction_date`; docstrings updated. In test_partition_key_generation.py: `EXTRACTION_DATE`, test rename and `extraction_date_path`; in test_sinks.py: test rename to `key_contains_extraction_date` and assert message. All 107 target-gcs tests pass.
- **Documentation:** docs/AI_CONTEXT/AI_CONTEXT_target-gcs.md: signature and role text use `extraction_date` and "extraction date"; GCSSink and Hive partitioning sections updated. loaders/target-gcs/CHANGELOG.md: new ### Changed entry for partition-path-extraction-date-clarity.
