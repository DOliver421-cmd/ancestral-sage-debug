"""
WAI Institute Contract Templates
Actual legal contract templates for subscriptions, enterprise, research, etc.
"""

from datetime import datetime, timedelta
from typing import Dict, Any


class ContractTemplate:
    """Base contract template class"""

    @staticmethod
    def render(data: Dict[str, Any]) -> str:
        """Render template with provided data"""
        raise NotImplementedError


class ConsumerSubscriptionAgreement(ContractTemplate):
    """
    Consumer Subscription Terms of Service
    For Basic/Advanced/Premium tier users
    """

    @staticmethod
    def render(data: Dict[str, Any]) -> str:
        """
        Required data:
        {
            "user_name": "...",
            "user_email": "...",
            "tier": "basic|advanced|premium",
            "price": 9.99,
            "billing_cycle": "monthly",
            "start_date": "2026-05-22",
            "end_date": "2026-06-22",
        }
        """
        user_name = data.get("user_name", "User")
        user_email = data.get("user_email", "")
        tier = data.get("tier", "basic").title()
        price = data.get("price", 0)
        billing_cycle = data.get("billing_cycle", "monthly").title()
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")

        template = f"""
SUBSCRIPTION AGREEMENT - WAI INSTITUTE

This Subscription Agreement ("Agreement") is entered into as of {start_date}
between WAI Institute ("Provider") and {user_name} ("Customer").

1. SUBSCRIPTION TIER
   Customer subscribes to the {tier} tier at ${price} per {billing_cycle.lower()}.

2. BILLING PERIOD
   Subscription begins: {start_date}
   Subscription ends: {end_date} (subject to renewal or cancellation)

3. PAYMENT TERMS
   - Payment is due on the first day of each billing cycle
   - Automatic renewal: This subscription renews automatically unless cancelled
   - Cancellation: Customer may cancel anytime with 30 days notice

4. SERVICE DESCRIPTION
   The WAI Institute provides:
   - Access to the Sage advisory service
   - Creator marketplace (if applicable to tier)
   - Research and insights (if applicable to tier)
   - Premium features (if applicable to tier)

5. LIABILITY & WARRANTIES
   DISCLAIMER: Sage is NOT a substitute for professional advice.

   Sage provides advisory information only. Provider makes NO WARRANTY that:
   - Sage recommendations will be effective
   - Sage recommendations are appropriate for your situation
   - Following Sage recommendations will produce desired outcomes

   LIMITATION OF LIABILITY: Provider shall not be liable for:
   - Any indirect, incidental, or consequential damages
   - Loss of profits, loss of data, or business interruption
   - Any damages arising from your reliance on Sage recommendations

   Provider's total liability is limited to the amount paid for the subscription.

6. ACCEPTABLE USE POLICY
   Customer agrees NOT to:
   - Use the service for illegal purposes
   - Harass, threaten, or abuse other users
   - Attempt to hack, reverse-engineer, or bypass security
   - Scrape or extract data without authorization
   - Transmit malware or harmful code

   Violation may result in immediate account suspension.

7. PRIVACY & DATA
   - Customer data is encrypted at rest and in transit
   - Provider will not share customer data with third parties without consent
   - Customer can request data export or deletion per GDPR/CCPA
   - See Privacy Policy for complete details

8. TERMINATION
   Provider may terminate this Agreement if Customer:
   - Violates the Acceptable Use Policy
   - Fails to pay after 30 days notice
   - Engages in fraudulent activity

   Upon termination, Customer loses access to the service.
   Provider retains the right to retain audit logs for 1 year.

9. MODIFICATIONS
   Provider reserves the right to modify this Agreement with 30 days written notice.
   Continued use of the service constitutes acceptance of modified terms.

10. GOVERNING LAW
    This Agreement is governed by the laws of Delaware.
    Any disputes shall be resolved through binding arbitration.

CUSTOMER SIGNATURE:
{user_name} ({user_email})
Signed: _______________
Date: __________________

PROVIDER SIGNATURE:
WAI Institute
Signed by: CEO
Date: {start_date}
"""
        return template


class EnterpriseSwSoftwareLicenseAgreement(ContractTemplate):
    """
    Enterprise Software License Agreement
    For organization-wide licensing of WAI platform
    """

    @staticmethod
    def render(data: Dict[str, Any]) -> str:
        """
        Required data:
        {
            "company_name": "...",
            "company_address": "...",
            "seats": 100,
            "annual_price": 50000,
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "features": ["sage", "research", "dashboards"],
        }
        """
        company = data.get("company_name", "Customer")
        seats = data.get("seats", 1)
        price = data.get("annual_price", 0)
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        features = ", ".join(data.get("features", []))

        template = f"""
ENTERPRISE SOFTWARE LICENSE AGREEMENT

This Enterprise Software License Agreement ("Agreement") is entered into as of {start_date}
between WAI Institute, Inc. ("Provider") and {company} ("Customer").

1. LICENSED SOFTWARE
   Provider grants Customer a non-exclusive, non-transferable license to use
   the WAI platform including the following features:
   - {features}

2. LICENSE SCOPE
   - Licensed Users: Up to {seats} named users
   - Term: {start_date} to {end_date} (one year)
   - Renewal: Automatic renewal unless terminated by either party with 90 days notice
   - Geographic Scope: Worldwide

3. FEES
   - Annual License Fee: ${price:,.2f}
   - Payment Terms: Net 30 (due within 30 days of invoice)
   - Renewal: Price may increase up to 10% annually
   - Additional Seats: ${price / seats:,.2f} per additional seat

4. IMPLEMENTATION & SUPPORT
   - Provider includes 40 hours of implementation services
   - Dedicated support: Monday-Friday, 9am-5pm PT
   - Critical issues: 1-hour response time
   - Non-critical issues: 24-hour response time

5. SERVICE LEVEL AGREEMENT (SLA)
   Provider commits to:
   - 99.5% uptime (measured monthly)
   - Daily backups with 4-hour recovery time
   - Security audits annually
   - Data encryption at rest and in transit

   If uptime falls below 99.5%, Customer receives:
   - 1-2% uptime miss: 10% of monthly fee credit
   - 2-5% uptime miss: 25% of monthly fee credit
   - >5% uptime miss: Full month fee credit

6. DATA RIGHTS & OWNERSHIP
   - Customer Data: Customer retains all ownership of business data
   - Provider's Rights: Provider may use aggregate, anonymized data for research
   - Data Subpoena: Provider will notify Customer of government data requests
   - Data Breach: Provider will notify Customer within 24 hours of discovery

7. SECURITY REQUIREMENTS
   Provider implements:
   - SOC 2 Type II certification
   - Annual penetration testing
   - Employee background checks
   - Data encryption (AES-256)
   - Two-factor authentication
   - Access logging and monitoring
   - Incident response plan

8. RESTRICTIONS
   Customer shall NOT:
   - Reverse engineer or modify the software
   - Remove or alter copyright notices
   - Use the software for competitive purposes
   - Resell or redistribute the software
   - Access unauthorized data

9. WARRANTY & DISCLAIMERS
   Provider warrants that:
   - Software will perform substantially as documented
   - Software does not infringe on third-party IP

   DISCLAIMER: Software provided "AS-IS" without other warranties.
   Provider makes NO WARRANTY of merchantability or fitness for purpose.

10. LIMITATION OF LIABILITY
    Total liability of Provider: Capped at amount paid in previous 12 months.

    Provider NOT liable for:
    - Indirect or consequential damages
    - Loss of profits, data, or revenue
    - Business interruption
    - Customer's misuse of software

11. TERMINATION
    Either party may terminate with:
    - 90 days written notice for convenience
    - Immediate notice for material breach (with 30 days to cure)

    Upon termination:
    - Customer access discontinued
    - Provider retains audit logs for 1 year
    - Customer may request data export (within 30 days)

12. RENEWAL
    Automatic renewal unless:
    - Either party provides 90 days written notice of non-renewal
    - Renewal pricing provided at least 60 days in advance
    - Customer may request custom pricing for large deployments

13. CONFIDENTIALITY
    Each party protects the other's confidential information.
    Exceptions: Publicly available information or required by law.

14. GOVERNING LAW
    This Agreement governed by Delaware law.
    Disputes resolved through binding arbitration (not courts).
    Each party bears its own legal fees.

15. AMENDMENT
    Modifications require written agreement signed by both parties.
    Provider may modify terms with 90 days notice.

CUSTOMER SIGNATURE:
Company: {company}
By: _______________________
Title: _______________________
Date: _______________________

PROVIDER SIGNATURE:
WAI Institute, Inc.
By: _______________________
Title: CEO
Date: {start_date}
"""
        return template


class ResearchDataLicenseAgreement(ContractTemplate):
    """
    Academic Research Data Licensing Agreement
    For university/research institution access to anonymized data
    """

    @staticmethod
    def render(data: Dict[str, Any]) -> str:
        """
        Required data:
        {
            "institution_name": "...",
            "principal_investigator": "...",
            "research_topic": "...",
            "duration_years": 2,
            "annual_fee": 50000,
        }
        """
        institution = data.get("institution_name", "Institution")
        pi = data.get("principal_investigator", "")
        topic = data.get("research_topic", "")
        years = data.get("duration_years", 1)
        fee = data.get("annual_fee", 0)

        template = f"""
RESEARCH DATA LICENSE AGREEMENT

This Research Data License Agreement ("Agreement") is between WAI Institute ("Provider")
and {institution} ("Licensee"), represented by {pi}.

1. RESEARCH TOPIC
   Licensee proposes to conduct research on: {topic}

2. DATA LICENSE
   Provider grants Licensee a non-exclusive license to:
   - Access anonymized, aggregated datasets from WAI platform
   - Use data for academic research and publication
   - Share anonymized data with collaborators within Licensee's institution

   Licensee shall NOT:
   - Attempt to re-identify individuals in the data
   - Combine data with other sources to identify individuals
   - Use data for commercial purposes
   - Transfer data outside the research team

3. TERM
   License term: {years} year(s)
   Annual fee: ${fee:,.2f}
   Renewal: Automatic unless terminated by either party with 90 days notice

4. ANONYMIZATION GUARANTEE
   Provider guarantees:
   - All direct identifiers removed (name, ID, email, etc.)
   - All quasi-identifiers aggregated or suppressed
   - No personal health information (PHI) included
   - Data meets HIPAA Safe Harbor standards (if applicable)

5. PUBLICATION & ATTRIBUTION
   Licensee agrees to:
   - Cite WAI Institute in all publications using this data
   - Include the following citation:
     "Data provided by WAI Institute under research license agreement"
   - Provide preprint to WAI 30 days before publication (for review only)
   - Notify WAI of any identified data quality issues

6. DATA SECURITY
   Licensee shall:
   - Store data on secure, encrypted servers
   - Limit access to authorized research team members
   - Maintain audit logs of data access
   - Delete data within 30 days of project completion
   - Not share with unauthorized parties

7. BREACH NOTIFICATION
   If Licensee suspects a data breach or unauthorized access:
   - Notify WAI within 24 hours
   - Provide details of breach and affected data
   - Cease data access immediately
   - Cooperate with WAI's investigation

8. DATA RETURN & DESTRUCTION
   Upon termination or project completion:
   - Licensee will permanently delete all copies of data
   - Confirm deletion in writing
   - Data may be archived (encrypted) for audit purposes only
   - Deletions must occur within 30 days

9. INTELLECTUAL PROPERTY
   - Provider retains all IP rights to the data
   - Licensee retains IP rights to research findings
   - Publication of findings permitted (with attribution)
   - Provider may not use Licensee's research results without permission

10. LIMITATION OF LIABILITY
    Provider provides data "AS-IS" without warranties.
    Provider not liable for data quality, completeness, or accuracy.
    Licensee responsible for independent data validation.

11. TERMINATION
    Either party may terminate with:
    - 30 days written notice for convenience
    - Immediate notice for breach

    Upon termination, all data must be deleted within 30 days.

12. CONFIDENTIALITY
    Both parties protect each other's confidential information.

13. GOVERNING LAW
    Delaware law governs this Agreement.
    Disputes resolved through binding arbitration.

14. IRREVOCABLE RESTRICTIONS
    These restrictions survive termination:
    - No re-identification attempts
    - No commercial use
    - No data transfer outside institution
    - Permanent deletion of data

LICENSEE SIGNATURE:
Institution: {institution}
Principal Investigator: {pi}
By: _______________________
Date: _______________________

PROVIDER SIGNATURE:
WAI Institute
By: _______________________
Title: CEO
Date: ________________
"""
        return template


# Helper function to generate contracts
def generate_contract(contract_type: str, data: Dict[str, Any]) -> str:
    """
    Generate a contract of the specified type

    Args:
        contract_type: 'consumer', 'enterprise', 'research', 'license', 'creator'
        data: Dictionary with template variables

    Returns:
        Rendered contract text
    """
    contracts = {
        "consumer": ConsumerSubscriptionAgreement,
        "enterprise": EnterpriseSwSoftwareLicenseAgreement,
        "research": ResearchDataLicenseAgreement,
    }

    contract_class = contracts.get(contract_type)
    if not contract_class:
        raise ValueError(f"Unknown contract type: {contract_type}")

    return contract_class.render(data)
