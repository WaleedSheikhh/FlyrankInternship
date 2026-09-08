import json
from pydantic import ValidationError
from app.llm.schema import EnrichmentOutput

fake_bad_output = '{"category": "mystery-thriller", "summary": "test", "quality_flags": []}'

try:
    parsed = json.loads(fake_bad_output)
    result = EnrichmentOutput(**parsed)
    print("Unexpectedly valid:", result)
except ValidationError as e:
    print("Validation correctly failed:")
    print(e)
    