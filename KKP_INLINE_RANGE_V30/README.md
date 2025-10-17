
# Inline Range → HH (V30)

Drop-in module that appends the selected range (from your range table UI) next to each manual action in the HH text.

## Quick test

```bash
python demo.py
```

## Integrate

1) Copy the `inline_range_hh` folder into your project (next to your UI code).
2) In your "Manuális bevitel" dialog's HH-generate handler, gather the ranges the user picked per action into a `dict`, where keys match the start of the HH action line (e.g., `"UTG bets"`, `"BB raises"`, `"UTG calls"`).
3) Call:

```python
from inline_range_hh import inject_ranges_into_hh

updated_hh = inject_ranges_into_hh(original_hh_text, assigned_ranges)
self.hhTextEdit.setPlainText(updated_hh)
```

- The function only appends once per line: ` [range: ...]`
- Hands should be standard codes: `AA, AKs, AKo, KQs, ...`

If your UI stores a 13×13 selection of cells instead of hand codes, convert them once to list of hands and pass that list.
```

