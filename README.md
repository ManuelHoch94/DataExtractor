# DataExtractor

Modular PDF data extraction engine with AI-powered index mapping, built on the Claude API.

## Architecture

```
data_extractor/
├── core/          # Models, exceptions, orchestrator
├── config/        # Pydantic-settings based configuration
├── readers/       # Abstract reader + PDF implementation
├── processors/    # Text cleaner + AI index mapper (Claude)
├── extractors/    # Field extractor (adapter over IndexMapper)
└── utils/         # Shared helpers
```

### Data flow

```
PDF file
  └─► PdfReader          →  ReadResult (raw text, page count, metadata)
        └─► TextProcessor  →  clean text
              └─► FieldExtractor / IndexMapper (Claude API)
                    └─► list[ExtractedField]
                          └─► ExtractionResult.to_index_dict()
```

## Quick start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Configure
cp .env .env
# Add your ANTHROPIC_API_KEY to .env

# 3. Run tests
pytest
```

## Usage

```python
from pathlib import Path
from data_extractor.config.settings import get_settings
from data_extractor.core.models import ExtractionRequest
from data_extractor.core.orchestrator import Orchestrator

settings = get_settings()
orch = Orchestrator.from_settings(settings)

result = orch.run(ExtractionRequest(
    file_path=Path("invoice.pdf"),
    schema_definition={
        "invoice_number": "The unique invoice identifier",
        "amount":         "Total amount due including taxes",
        "vendor":         "Name of the issuing company",
    },
))

print(result.to_index_dict())
# {"invoice_number": "INV-2024-001", "amount": "1.500,00 EUR", "vendor": "Acme GmbH"}
```

## Configuration

| Env var | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Claude model |
| `EXTRACTION_CONFIDENCE_THRESHOLD` | `0.5` | Min confidence to include a field |
| `EXTRACTION_MAX_TOKENS` | `2048` | Max tokens for Claude responses |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Testing

```bash
pytest                          # run all tests with coverage
pytest tests/unit               # unit tests only
pytest tests/integration        # integration tests only
pytest --cov-report=html        # HTML coverage report
```

Coverage target: **≥ 80 %**
