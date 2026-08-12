# Kujo DocGen

- Root: `src`
- Languages: kujo
- Symbols: 367
- Gaps: 0

## main (kujo)

### validate_value

- Kind: Function
- Visibility: Private
- Source: `main.kujo:5`
- Signature: `func(value, schema, label)`

Validate one decoded artifact value against its checked-in JSON Schema.

### validate_run_schemas

- Kind: Function
- Visibility: Private
- Source: `main.kujo:14`
- Signature: `func(run_path)`

Apply Kujo's Draft 2020-12 validator to every primary run artifact.

### main

- Kind: Function
- Visibility: Private
- Source: `main.kujo:40`
- Signature: `func()`

Delegate protocol work, then enforce Kujo-native artifact contracts.

