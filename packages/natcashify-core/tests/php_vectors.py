import json
from pathlib import Path
from typing import Any

from natcashify.core.config import Language, MerchantConfig

_FIXTURE = Path(__file__).parent / "fixtures" / "php_vectors.json"
_TEXT = _FIXTURE.read_text(encoding="utf-8")

VECTORS: dict[str, list[dict[str, Any]]] = json.loads(_TEXT, parse_float=str)
RAW_VECTORS: dict[str, list[dict[str, Any]]] = json.loads(_TEXT)

CONFIG = MerchantConfig(
    private_key="private-key-1",
    partner_code="PARTNER1",
    function_code="FUNC1",
    username="merchant",
    password="s3cr3t",
    callback_url="https://shop.example/natcash/callback",
)


def config_for(case: dict[str, Any]) -> MerchantConfig:
    inputs = case["inputs"]
    return MerchantConfig(
        private_key=CONFIG.private_key,
        partner_code=CONFIG.partner_code,
        function_code=CONFIG.function_code,
        username=CONFIG.username,
        password=CONFIG.password,
        callback_url=CONFIG.callback_url,
        payer_pays_fee=inputs["enableFee"],
        language=Language(inputs["language"]),
    )
