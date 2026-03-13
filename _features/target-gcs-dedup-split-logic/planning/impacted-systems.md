# Impacted Systems: target-gcs-dedup-split-logic

Refactoring scope: `loaders/target-gcs/target_gcs/` and `target_gcs/helpers/`. No external libraries; behaviour preserved.

---

## 1. Duplicated logic (concrete locations)

### 1.1 Handle flush and close

- **File:** `target_gcs/sinks.py`
- **Locations:**
  - `_rotate_to_new_chunk()` (lines 191–194): if handle exists → flush (if hasattr) → close → set `_gcs_write_handle = None`
  - `_close_handle_and_clear_state()` (lines 201–205): same block
- **Duplication:** Identical 4-line block for “flush then close handle and clear reference”.

### 1.2 Key prefix and path normalization

- **File:** `target_gcs/sinks.py`
- **Locations:**
  - `_build_key_for_record()` (lines 129–131): `f"{self.config.get('key_prefix', '')}/{base}".replace("//", "/").lstrip("/")`
  - `key_name` property (lines 150–154): same pattern with `prefixed_key_name` and `base_key_name`
- **Duplication:** Same “prefix + base, replace double slash, strip leading slash” logic.

### 1.3 Record serialization and write

- **File:** `target_gcs/sinks.py`
- **Locations:**
  - `_process_record_single_or_chunked()` (lines 219–224): `orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE, default=_json_default)` then `self.gcs_write_handle.write(...)`
  - `_process_record_hive_partitioned()` (lines 271–276): identical call
- **Duplication:** Same “serialize record to JSONL and write to current handle”.

### 1.4 Rotate-if-at-limit check

- **File:** `target_gcs/sinks.py`
- **Locations:**
  - `_process_record_single_or_chunked()` (lines 216–222): get `max_records`, if set and `_records_written_in_current_file >= max_records` then `_rotate_to_new_chunk()`
  - `_process_record_hive_partitioned()` (lines 258–265): same block
- **Duplication:** Same “maybe rotate when record count reaches max_records_per_file”.

### 1.5 `DEFAULT_PARTITION_DATE_FORMAT` constant

- **Files:**
  - `target_gcs/sinks.py` line 23: local definition
  - `target_gcs/helpers/partition_path.py` line 5: definition and use in `get_partition_path_from_schema_and_record`
- **Duplication:** Constant defined in two places; sinks could import from helpers only.

### 1.6 Partition schema validation structure (properties, required, non-null type)

- **File:** `target_gcs/helpers/partition_schema.py`
- **Locations:**
  - `validate_partition_fields_schema()`: for each field → properties lookup, required check, prop_schema type → types list → non_null filter → reject if null-only
  - `validate_partition_date_field_schema()`: same pattern for single field (properties, required, prop_schema type, types, non_null, then extra date-parseable check)
- **Duplication:** Shared “field in properties, in required, has at least one non-null type” pattern; only the error messages and the extra date-parseable logic differ.

---

## 2. Switch / branch logic (concrete locations)

### 2.1 `key_name` property

- **File:** `target_gcs/sinks.py` (lines 142–168)
- **Logic:** If `hive_partitioned`: return `self._key_name`. Else: if not `_key_name`, compute key (template, format_map, prefix/normalize, assign `_key_name`), then return `_key_name`.
- **Switch point:** Two branches; the non-hive branch is a large inline block (template, date, format_map, prefix, format).

### 2.2 `GCSSink.__init__` hive setup

- **File:** `target_gcs/sinks.py` (lines 68–77)
- **Logic:** If `config.get("hive_partitioned")`: set `_current_partition_path = None`, get `x_partition_fields`, if non-empty list call `validate_partition_fields_schema(...)`.
- **Switch point:** Init-time branch; hive-specific state and validation in the constructor.

### 2.3 `process_record` dispatcher

- **File:** `target_gcs/sinks.py` (lines 286–296)
- **Logic:** If `hive_partitioned` → `_process_record_hive_partitioned`, else → `_process_record_single_or_chunked`.
- **Status:** Already split into two named methods; dispatcher is thin. No change required except possibly extracting shared behaviour (see 1.3, 1.4).

---

## 3. Summary table

| Category        | Module / file              | Functions / areas affected                                      |
|----------------|----------------------------|------------------------------------------------------------------|
| Duplication    | `sinks.py`                 | handle close block, key prefix/normalize, orjson write, rotate check, constant |
| Duplication    | `helpers/partition_path.py`| `DEFAULT_PARTITION_DATE_FORMAT` (single source of truth)        |
| Duplication    | `helpers/partition_schema.py` | Two validators sharing “field in schema, required, non-null” pattern |
| Switch logic   | `sinks.py`                 | `key_name` (hive vs non-hive), `__init__` (hive setup)           |
