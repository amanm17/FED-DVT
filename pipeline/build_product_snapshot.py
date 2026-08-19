import json
from pathlib import Path
import pandas as pd

SOURCE = Path("data/raw/comtrade/2025_699_847130_M_ALL.parquet")
OUT = Path("data/processed/847130_india_2025_import_snapshot.json")

df = pd.read_parquet(SOURCE)

world = df[df["partnerCode"] == 0]

if len(world) != 1:
    raise ValueError(f"Expected exactly one World row, found {len(world)}")

world_row = world.iloc[0]
total = float(world_row["primaryValue"])

partners = (
    df[df["partnerCode"] != 0]
    .copy()
    .sort_values("primaryValue", ascending=False)
)

partners["share"] = partners["primaryValue"] / total

top_partners = []

for _, r in partners.head(10).iterrows():
    top_partners.append({
        "partnerCode": int(r["partnerCode"]),
        "partnerISO": r["partnerISO"],
        "partner": r["partnerDesc"],
        "tradeValue": float(r["primaryValue"]),
        "share": float(r["share"]),
        "quantity": None if pd.isna(r["qty"]) else float(r["qty"]),
        "quantityUnit": r["qtyUnitAbbr"],
        "netWeightKg": None if pd.isna(r["netWgt"]) else float(r["netWgt"]),
        "quantityEstimated": bool(r["isQtyEstimated"]),
        "netWeightEstimated": bool(r["isNetWgtEstimated"]),
    })

shares = partners["share"].dropna()

hhi = float((shares ** 2).sum())

if hhi >= 0.25:
    concentration = "High"
elif hhi >= 0.15:
    concentration = "Moderate"
else:
    concentration = "Low"

snapshot = {
    "product": {
        "hsCode": str(world_row["cmdCode"]),
        "description": world_row["cmdDesc"],
        "classification": world_row["classificationCode"],
        "level": int(world_row["aggrLevel"]),
    },
    "context": {
        "reporterCode": int(world_row["reporterCode"]),
        "reporterISO": world_row["reporterISO"],
        "reporter": world_row["reporterDesc"],
        "year": int(world_row["refYear"]),
        "flow": world_row["flowDesc"],
    },
    "headline": {
        "tradeValue": total,
        "quantity": None if pd.isna(world_row["qty"]) else float(world_row["qty"]),
        "quantityUnit": world_row["qtyUnitAbbr"],
        "netWeightKg": None if pd.isna(world_row["netWgt"]) else float(world_row["netWgt"]),
    },
    "supplierConcentration": {
        "largestSupplier": top_partners[0]["partner"] if top_partners else None,
        "largestSupplierShare": top_partners[0]["share"] if top_partners else None,
        "top3Share": float(partners.head(3)["share"].sum()),
        "hhi": hhi,
        "classification": concentration,
    },
    "topPartners": top_partners,
    "provenance": {
        "source": "UN Comtrade",
        "sourceFile": str(SOURCE),
        "reportedAggregate": bool(world_row["isAggregate"]),
        "quantityEstimated": bool(world_row["isQtyEstimated"]),
        "netWeightEstimated": bool(world_row["isNetWgtEstimated"]),
    }
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(snapshot, indent=2))

print(f"Wrote: {OUT}")
print()
print(f"HS: {snapshot['product']['hsCode']}")
print(f"India imports: ${total/1e9:.3f}bn")
print(
    f"Largest supplier: "
    f"{snapshot['supplierConcentration']['largestSupplier']} "
    f"({snapshot['supplierConcentration']['largestSupplierShare']:.1%})"
)
print(f"Top 3 share: {snapshot['supplierConcentration']['top3Share']:.1%}")
print(f"HHI: {hhi:.3f}")
print(f"Concentration: {concentration}")
