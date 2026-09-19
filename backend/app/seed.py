from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Contract, PolicyRule

POLICY_RULES = [
    dict(
        topic="auto_renewal",
        guidance="Auto-renewal without an opt-out window locks you into another term before you notice.",
        severity="high",
        risk_keywords="automatically renew,auto-renew,automatically extended",
        fallback_language="This Agreement renews only upon mutual written consent given at least 30 days before the then-current term ends.",
    ),
    dict(
        topic="liability_cap",
        guidance="An uncapped or vendor-favorable liability clause exposes you to damages far beyond the contract value.",
        severity="high",
        risk_keywords="unlimited liability,liability shall not be limited,no cap on liability",
        fallback_language="Each party's aggregate liability is capped at the fees paid in the 12 months preceding the claim.",
    ),
    dict(
        topic="payment_terms",
        guidance="Short payment windows or steep unilateral late fees create cash-flow risk for the customer.",
        severity="medium",
        risk_keywords="due upon receipt,net 10,late fee of 5%,interest of 1.5% per month",
        fallback_language="Payment is due net 30 from invoice date, with a maximum late fee of 1% per month.",
    ),
    dict(
        topic="data_processing",
        guidance="Vague data processing terms can leave you non-compliant with your own customers' data protection obligations.",
        severity="high",
        risk_keywords="may use customer data for any purpose,may share data with third parties,no obligation to delete data",
        fallback_language="Vendor processes customer data solely to provide the service under a data processing addendum meeting GDPR/CCPA requirements, and deletes it within 30 days of termination.",
    ),
    dict(
        topic="termination_for_convenience",
        guidance="One-sided termination rights let the vendor walk away without notice while the customer stays locked in.",
        severity="medium",
        risk_keywords="vendor may terminate at any time,in its sole discretion,without cause and without notice",
        fallback_language="Either party may terminate for convenience with 60 days' written notice.",
    ),
]

CONTRACTS = [
    dict(
        vendor_name="Northwind Analytics",
        raw_text=(
            "This Agreement will automatically renew for successive one-year terms unless either "
            "party provides notice. Vendor's liability shall not be limited under any circumstances "
            "arising from this Agreement. All invoices are due upon receipt. Vendor may use customer "
            "data for any purpose related to improving its products. Vendor may terminate this "
            "Agreement at any time in its sole discretion."
        ),
    ),
    dict(
        vendor_name="Ferrous Logistics API",
        raw_text=(
            "Payment is due net 30 from the invoice date. Either party may terminate this Agreement "
            "for convenience with 60 days written notice. Vendor's data processing addendum meets "
            "GDPR requirements and vendor deletes customer data within 30 days of termination. This "
            "Agreement does not renew automatically and each party's liability is capped at fees paid "
            "in the preceding 12 months."
        ),
    ),
    dict(
        vendor_name="Bramblewick Payroll",
        raw_text=(
            "This Agreement is automatically extended each year unless cancelled in writing 90 days "
            "prior. Any invoice unpaid after 10 days accrues a late fee of 5% plus interest of 1.5% "
            "per month. Vendor may share data with third parties for marketing purposes."
        ),
    ),
]


def get_or_create_policy_rule(session: Session, data: dict) -> PolicyRule:
    existing = session.exec(select(PolicyRule).where(PolicyRule.topic == data["topic"])).first()
    if existing:
        return existing
    rule = PolicyRule(**data)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def main() -> None:
    init_db()
    with Session(engine) as session:
        for data in POLICY_RULES:
            get_or_create_policy_rule(session, data)

        if not session.exec(select(Contract)).first():
            for data in CONTRACTS:
                session.add(Contract(**data))
            session.commit()

    print("Seeded policy playbook and sample contracts.")


if __name__ == "__main__":
    main()
