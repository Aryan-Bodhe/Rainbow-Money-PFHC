from collections import OrderedDict
from typing import Dict, Any, Tuple
from .benchmarking import get_benchmarks, analyse_benchmarks
from models.DerivedMetrics import PersonalFinanceMetrics


class FinancialFeedbackEngine:
    def __init__(self):
        self.priority_order = [
            'emergency_fund_ratio',
            'debt_income_ratio',
            'term_insurance_adequacy',
            'health_insurance_adequacy',
            'liquidity_ratio',
            'savings_income_ratio',
            'expense_income_ratio',
            'investment_income_ratio',
            'asset_liability_ratio',
            'housing_income_ratio',
            'retirement_adequacy',
            'net_worth_adequacy'
        ]
        # thresholds for real estate allocation
        self.real_estate_low = 0.20
        self.real_estate_high = 0.65

        self.feedback_templates = {
            'improvement': {
                'savings_income_ratio':
                    "Your savings rate of {value:.0%} is below the recommended level. Consider automating transfers to save at least 20% of your income monthly.",
                'investment_income_ratio':
                    "You're investing {value:.0%} of your income. Try increasing SIPs to 25-30% for better long-term growth.",
                'expense_income_ratio':
                    "Your expenses use {value:.0%} of your income. Review discretionary spending to save more.",
                'debt_income_ratio':
                    "Your debt payments use {value:.0%} of income. Focus on clearing your {highest_interest_debt} first.",
                'emergency_fund_ratio':
                    "Your emergency fund covers {value:.1f} months. The ideal is 6 months. Consider moving ₹{excess_amount:,.0f} to investments.",
                'liquidity_ratio':
                    "Your liquid assets cover {value:.1f} months of expenses. Ideal is 3-4 months. Redirect ₹{excess_amount:,.0f} to higher-yield options.",
                'asset_liability_ratio':
                    "Your liabilities are high relative to assets. Prioritize debt reduction to improve net worth.",
                'housing_income_ratio':
                    "Your housing costs use {value:.0%} of income. Consider refinancing if rates have dropped.",
                'health_insurance_adequacy':
                    "Your health cover of ₹{value:,.0f} may be insufficient. Consider increasing to ₹{recommended_cover:,.0f}.",
                'term_insurance_adequacy':
                    "Your term cover of ₹{value:,.0f} may leave dependents vulnerable. Aim for ₹{recommended_cover:,.0f}.",
                'net_worth_adequacy':
                    "Your net worth growth is below expectations. Review investment strategy with an advisor.",
                'retirement_adequacy':
                    "Your retirement fund is {value:.0%} complete. Increase monthly SIPs by ₹{additional_sip:,.0f}.",
                'excessive_emergency_fund':
                    "Your emergency fund covers {value:.1f} months – more than needed. Move ₹{excess_amount:,.0f} to higher-return instruments.",
                'excessive_liquidity':
                    "You have ₹{value:,.0f} in low-return liquid assets. Redirect ₹{excess_amount:,.0f} to balanced funds.",
                'overinsured_health':
                    "Your health cover of ₹{value:,.0f} exceeds needs. Reduce to ₹{optimal_cover:,.0f} and invest the savings.",
                'overinsured_term':
                    "Your term cover of ₹{value:,.0f} is higher than needed. Reduce to ₹{optimal_cover:,.0f}.",
                'overconservative_asset_allocation':
                    "Your portfolio is {debt:.0f}% debt-heavy for age {age}. Shift ₹{reallocation_amount:,.0f} to growth options."
            },
            'commendable': {
                'savings_income_ratio':
                    "Great job saving {value:.0%} of your income! This builds a strong financial foundation.",
                'investment_income_ratio':
                    "Well done investing {value:.0%} of income! This will grow significantly over time.",
                'expense_income_ratio':
                    "Excellent expense management at {value:.0%} of income! You're living within your means.",
                'debt_income_ratio':
                    "Good debt management at {value:.0%} of income! You're balancing credit wisely.",
                'emergency_fund_ratio':
                    "Your {value:.1f}-month emergency fund provides good security. Maintain this safety net.",
                'liquidity_ratio':
                    "Your {value:.1f}-month liquid reserve is well balanced. Keep this for unexpected needs.",
                'asset_liability_ratio':
                    "Strong asset-liability ratio! You're building wealth effectively.",
                'housing_income_ratio':
                    "Good housing cost control at {value:.0%} of income! This saves money for other goals.",
                'health_insurance_adequacy':
                    "Your ₹{value:,.0f} health cover provides solid protection. Review every 2-3 years.",
                'term_insurance_adequacy':
                    "Your ₹{value:,.0f} term cover offers strong family protection. Well planned!",
                'net_worth_adequacy':
                    "Your net worth growth is on track. Keep up the good wealth-building habits!",
                'retirement_adequacy':
                    "Your retirement fund is {value:.0%} complete. You're on track for comfortable retirement."
            }
        }

    def get_benchmark_data(self, pfm: PersonalFinanceMetrics) -> Dict[str, Tuple[float, float]]:
        return get_benchmarks(pfm)

    def determine_verdicts(self, pfm: PersonalFinanceMetrics) -> Dict[str, str]:
        return analyse_benchmarks(pfm)

    def identify_conservative_allocations(self, user_data: Dict[str, Any]) -> Dict[str, Dict]:
        findings: Dict[str, Dict] = {}
        expenses = user_data['expense_data']
        assets = user_data['asset_data']
        insurance = user_data['insurance_data']
        personal = user_data['personal_data']

        monthly_expenses = sum([
            expenses['housing_cost'],
            expenses['utilities_and_bills'],
            expenses['groceries_and_essentials'],
            expenses['discretionary_expense']
        ])

        # Overfunded emergency reserve
        emergency_fund = assets['total_emergency_fund']
        ideal_emergency = 6 * monthly_expenses
        excess_amount = emergency_fund - ideal_emergency
        if excess_amount > 0.3 * ideal_emergency:
            findings['excessive_emergency_fund'] = {
                'value': round(emergency_fund / monthly_expenses, 2),
                'excess_amount': round(excess_amount, 2)
            }

        # Excessive liquid assets
        liquid_assets = assets['total_savings_balance'] + emergency_fund
        ideal_liquid = 4 * monthly_expenses
        excess_liquid = liquid_assets - ideal_liquid
        if excess_liquid > 0.3 * ideal_liquid:
            findings['excessive_liquidity'] = {
                'value': round(liquid_assets, 2),
                'excess_amount': round(excess_liquid, 2)
            }

        # Overinsured health
        health_cover = insurance['total_medical_cover']
        ideal_health_cover = 1000000 + 500000 * personal['no_of_dependents']
        if health_cover > 1.5 * ideal_health_cover:
            findings['overinsured_health'] = {
                'value': health_cover,
                'excess_amount': round(health_cover - ideal_health_cover, 2),
                'optimal_cover': ideal_health_cover
            }

        # Overinsured term
        term_cover = insurance['total_term_cover']
        ideal_term_cover = 20 * user_data['income_data']['salaried_income']
        if term_cover > 1.5 * ideal_term_cover:
            findings['overinsured_term'] = {
                'value': term_cover,
                'excess_amount': round(term_cover - ideal_term_cover, 2),
                'optimal_cover': ideal_term_cover
            }

        return findings

    def get_highest_interest_debt(self, liabilities: Dict[str, float]) -> str:
        debt_rates = {
            'outstanding_credit_card_balance': 42,
            'outstanding_personal_loan_balance': 15,
            'outstanding_car_loan_balance': 12,
            'outstanding_home_loan_balance': 9
        }
        for debt, _ in sorted(debt_rates.items(), key=lambda x: x[1], reverse=True):
            if liabilities.get(debt, 0) > 0:
                return debt.replace('_', ' ').title()
        return "No Debt"

    def generate_asset_allocation_advice(self, user_data: Dict[str, Any]) -> str:
        personal = user_data['personal_data']
        risk_profile = personal['risk_profile']
        age = personal['age']

        base_allocations = {
            'Aggressive': {'equity': 80, 'debt': 10, 'gold': 5, 'real_estate': 5},
            'Moderate': {'equity': 60, 'debt': 25, 'gold': 5, 'real_estate': 10},
            'Conservative': {'equity': 40, 'debt': 40, 'gold': 10, 'real_estate': 10}
        }
        age_factor = max(0, (50 - age) / 10)
        allocation = base_allocations.get(risk_profile, base_allocations['Moderate']).copy()
        allocation['equity'] = min(90, allocation['equity'] + 5 * age_factor)
        allocation['debt'] = max(10, allocation['debt'] - 5 * age_factor)
        allocation['real_estate'] = max(self.real_estate_low * 100,
                                        min(self.real_estate_high * 100,
                                            allocation['real_estate'] + 5))

        return (
            f"Based on your {risk_profile.lower()} risk profile and age {age}, consider this allocation:\n"
            f"- Equity: {allocation['equity']}% (Growth potential)\n"
            f"- Debt: {allocation['debt']}% (Stability)\n"
            f"- Gold: {allocation['gold']}% (Inflation hedge)\n"
            f"- Real Estate: {allocation['real_estate']}% (Tangible assets)"
        )

    def generate_feedback(
        self,
        user_data: Dict[str, Any],
        pfm: PersonalFinanceMetrics
    ) -> Dict[str, list]:
        metrics = pfm.model_dump()
        verdicts = self.determine_verdicts(pfm)
        benchmarks = self.get_benchmark_data(pfm)

        commendable = OrderedDict()
        improvements = OrderedDict()
        personal = user_data['personal_data']

        context = {
            'monthly_expenses': metrics.get('total_monthly_expense', 0),
            'highest_interest_debt': self.get_highest_interest_debt(user_data['liability_data'])
        }

        for metric in self.priority_order:
            value = metrics.get(metric)
            verdict = verdicts.get(metric, '').lower()
            ctx = {**context, 'value': value}

            if metric in ('health_insurance_adequacy', 'term_insurance_adequacy'):
                lower, _ = benchmarks.get(metric, (0, 0))
                ctx['recommended_cover'] = lower

            if metric == 'emergency_fund_ratio':
                excess = max(0, (value * context['monthly_expenses']) - (6 * context['monthly_expenses']))
                ctx['excess_amount'] = round(excess, 2)
            elif metric == 'retirement_adequacy':
                additional = max(5000, (1 - value) * user_data['income_data']['salaried_income'] / 12)
                ctx['additional_sip'] = round(additional, 2)

            if 'urgent' in verdict or 'improvement' in verdict:
                template = self.feedback_templates['improvement'].get(metric)
                if template:
                    improvements[metric] = template.format(**ctx)
            elif 'good' in verdict or 'excellent' in verdict:
                template = self.feedback_templates['commendable'].get(metric)
                if template:
                    commendable[metric] = template.format(**ctx)

        # conservative allocations
        for alloc_key, details in self.identify_conservative_allocations(user_data).items():
            ctx = {**context, **details}
            template = self.feedback_templates['improvement'].get(alloc_key)
            if template:
                improvements[alloc_key] = template.format(**ctx)

        # debt-free special case
        if all(user_data['liability_data'].get(k, 0) == 0 for k in [
            'outstanding_credit_card_balance',
            'outstanding_personal_loan_balance',
            'outstanding_car_loan_balance',
            'outstanding_student_loan_balance',
            'outstanding_home_loan_balance'
        ]):
            commendable['debt_free'] = "Great work being debt-free! This significantly strengthens your financial position."

        # retirement priority for age >50
        if personal['age'] > 50 and metrics.get('retirement_adequacy', 0) < 0.8:
            gap = 1 - metrics['retirement_adequacy']
            additional_sip = max(10000, gap * metrics.get('total_monthly_income', 0) * 0.3)  
            improvements['retirement_priority'] = (
                f"Your retirement fund needs attention. Consider increasing SIPs by ₹{additional_sip:,.0f}/month."
            )

        # asset allocation advice
        improvements['asset_allocation'] = self.generate_asset_allocation_advice(user_data)

        # real estate recommendations
        re_pct = metrics.get('asset_class_distribution', {}).get('real_estate', 0)
        if re_pct < self.real_estate_low:
            improvements['real_estate'] = (
                f"Consider adding real estate to your portfolio (currently {re_pct:.0%})."
            )
        elif re_pct > self.real_estate_high:
            improvements['real_estate'] = (
                f"Your real estate allocation ({re_pct:.0%}) exceeds recommended maximum. Consider diversifying into financial assets."
            )

        return {
            'commendable_points': list(commendable.values()),
            'improvement_points': list(improvements.values())
        }
