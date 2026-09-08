import inspect
import importlib
from typing import Any

TARGETS = [
    (
        "DATA_QUALITY",
        "services.data_platform.quality",
        ["DataQualityEngine"],
    ),
    (
        "FINANCIAL_RATIOS",
        "services.financials.financial_ratios",
        ["FinancialRatios", "calculate_financial_ratios"],
    ),
    (
        "FINANCIAL_STATEMENTS",
        "services.financials.financial_statement",
        ["PeriodFinancials", "FinancialStatements"],
    ),
    (
        "NORMALIZATION",
        "services.financials.normalization",
        [
            "normalize_income_statement",
            "normalize_balance_sheet",
            "normalize_cash_flow",
            "normalize_financial_statements",
        ],
    ),
    (
        "FUNDAMENTAL_NORMALIZER",
        "services.fundamentals.normalizer",
        ["FinancialNormalizer"],
    ),
    (
        "ADVANCED_QUALITY",
        "services.ratios.quality_engine",
        ["AdvancedQualityEngine"],
    ),
    (
        "LEGACY_SCORE",
        "services.score_service",
        [
            "calculate_stability_score",
            "calculate_investment_score",
        ],
    ),
    (
        "FUNDAMENTAL_SCORE",
        "services.fundamental_score_service",
        ["calculate_fundamental_score"],
    ),
    (
        "FUNDAMENTAL_ENGINE",
        "services.scoring.fundamental",
        ["FundamentalScoreResult", "FundamentalScoringEngine"],
    ),
    (
        "RISK_ENGINE",
        "services.scoring.risk_scoring",
        ["RiskScoreResult", "RiskScoringEngine"],
    ),
    (
        "TECHNICAL_SCORE",
        "services.technical_score_service",
        ["calculate_technical_score"],
    ),
    (
        "SOTP_CANONICAL",
        "services.sotp.sotp_engine",
        [
            "SegmentValuation",
            "SOTPInput",
            "SOTPResult",
            "SOTPAggregator",
        ],
    ),
    (
        "SOTP_VALUATION",
        "services.valuation.sotp_engine",
        [
            "BaseValuationEngine",
            "SOTPValuationEngine",
        ],
    ),
    (
        "DCF_VALUATION",
        "services.valuation.dcf_engine",
        [
            "BaseValuationEngine",
            "DCFValuationEngine",
        ],
    ),
    (
        "DCF_ADAPTER",
        "services.valuation.dcf_adapter",
        ["DCFValuationEngine"],
    ),
]

def print_header(text):
    print("")
    print("=" * 72)
    print(text)
    print("=" * 72)

for group, module_name, names in TARGETS:

    print_header(group + " :: " + module_name)

    try:
        module = importlib.import_module(module_name)
        print("MODULE IMPORT: PASS")

    except Exception as exc:
        print("MODULE IMPORT: FAIL")
        print(type(exc).__name__ + ": " + str(exc))
        continue

    for name in names:

        print("")
        print("-" * 72)
        print("SYMBOL:", name)
        print("-" * 72)

        obj = getattr(module, name, None)

        if obj is None:
            print("NOT FOUND")
            continue

        print("TYPE:", type(obj))
        print("QUALNAME:", getattr(obj, "__qualname__", None))
        print("MODULE:", getattr(obj, "__module__", None))

        try:
            print("SIGNATURE:", inspect.signature(obj))
        except Exception as exc:
            print("SIGNATURE: unavailable:", exc)

        if inspect.isclass(obj):

            print("")
            print("CLASS METHODS:")

            for method_name, method in inspect.getmembers(
                obj,
                predicate=inspect.isfunction
            ):

                if method_name.startswith("_") and method_name not in (
                    "__init__",
                ):
                    continue

                try:
                    sig = inspect.signature(method)
                except Exception:
                    sig = "?"

                print("  ", method_name, sig)

                if method_name in (
                    "evaluate",
                    "calculate",
                    "value",
                    "normalize",
                    "inspect_metric",
                    "summary",
                ):

                    try:
                        source = inspect.getsource(method)
                        print("")
                        print("SOURCE:")
                        print(source[:12000])
                    except Exception as exc:
                        print("SOURCE UNAVAILABLE:", exc)

        elif inspect.isfunction(obj):

            try:
                source = inspect.getsource(obj)
                print("")
                print("SOURCE:")
                print(source[:12000])
            except Exception as exc:
                print("SOURCE UNAVAILABLE:", exc)

# ============================================================
# EROS PIPELINE / API
# ============================================================

print_header("CURRENT EROS PIPELINE")

try:
    module = importlib.import_module("eros.decision.pipeline")
    print("PIPELINE IMPORT: PASS")

    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        if inspect.isfunction(obj) or inspect.isclass(obj):
            try:
                print(name, "::", inspect.signature(obj))
            except Exception:
                print(name)

except Exception as exc:
    print("PIPELINE IMPORT: FAIL")
    print(type(exc).__name__ + ": " + str(exc))

print_header("CURRENT EROS API")

try:
    module = importlib.import_module("eros.api.service")
    print("API IMPORT: PASS")

    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        if inspect.isfunction(obj) or inspect.isclass(obj):
            try:
                print(name, "::", inspect.signature(obj))
            except Exception:
                print(name)

except Exception as exc:
    print("API IMPORT: FAIL")
    print(type(exc).__name__ + ": " + str(exc))

# ============================================================
# CONTRACTS
# ============================================================

print_header("EROS CONTRACTS")

try:
    module = importlib.import_module("eros.contracts.models")
    print("CONTRACT IMPORT: PASS")

    for name, obj in inspect.getmembers(module, inspect.isclass):

        if obj.__module__ != module.__name__:
            continue

        print("")
        print("MODEL:", name)

        try:
            print("SIGNATURE:", inspect.signature(obj))
        except Exception:
            pass

        try:
            print("FIELDS:")
            annotations = getattr(obj, "__annotations__", {})
            for key, value in annotations.items():
                print("  ", key, ":", value)
        except Exception:
            pass

except Exception as exc:
    print("CONTRACT IMPORT: FAIL")
    print(type(exc).__name__ + ": " + str(exc))

print("")
print("=" * 72)
print("END PHASE 5C ENGINE CONTRACT INSPECTION")
print("=" * 72)
