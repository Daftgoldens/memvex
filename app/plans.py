"""
Kronvex — Définition des plans et quotas.
Pour modifier les limites d'un plan : édite PLANS ci-dessous.
Stripe webhook appellera create_api_key(plan="growth") automatiquement.
"""
from typing import TypedDict


class Plan(TypedDict):
    name: str
    price_eur: int | None   # mensuel en euros, None = sur devis
    agents: int | None      # None = illimité
    memories: int | None    # None = illimité
    session_filtering: bool
    custom_embeddings: bool
    gdpr_dpa: bool
    sla_pct: float | None


PLANS: dict[str, Plan] = {
    "demo": {
        "name": "Demo",
        "price_eur": 0,
        "agents": 1,
        "memories": 100,
        "session_filtering": False,
        "custom_embeddings": False,
        "gdpr_dpa": False,
        "sla_pct": None,
    },
    "starter": {
        "name": "Starter",
        "price_eur": 99,
        "agents": 1,
        "memories": 10_000,
        "session_filtering": False,
        "custom_embeddings": False,
        "gdpr_dpa": False,
        "sla_pct": None,
    },
    "growth": {
        "name": "Growth",
        "price_eur": 499,
        "agents": 5,
        "memories": 100_000,
        "session_filtering": True,
        "custom_embeddings": False,
        "gdpr_dpa": False,
        "sla_pct": 99.9,
    },
    "scale": {
        "name": "Scale",
        "price_eur": 1499,
        "agents": 20,
        "memories": None,       # illimité
        "session_filtering": True,
        "custom_embeddings": True,
        "gdpr_dpa": True,
        "sla_pct": 99.9,
    },
    "enterprise": {
        "name": "Enterprise",
        "price_eur": None,
        "agents": None,         # illimité
        "memories": None,       # illimité
        "session_filtering": True,
        "custom_embeddings": True,
        "gdpr_dpa": True,
        "sla_pct": None,        # SLA négocié
    },
}


def get_plan(plan_name: str) -> Plan:
    """Retourne la config du plan. Défaut : demo si inconnu."""
    return PLANS.get(plan_name, PLANS["demo"])
