AREAS_FOR_IMPROVEMENT = {
    "emergency_fund_ratio": 
    {
        "extremely_low": "Your emergency fund covers only {user_value:.1f} months, which is dangerously low. Build at least ₹{gap_amt:,.0f} to reach 6 months' worth of expenses.",
        "low": "You have {user_value:.1f} months of emergency savings. Increase it by ₹{gap_amt:,.0f} to hit the 6-month safety buffer.",
        "high": "Your emergency fund covers {user_value:.1f} months—more than required. Consider shifting ₹{gap_amt:,.0f} to investments for better returns.",
        "extremely_high": "You’ve overfunded your emergency reserves ({user_value:.1f} months). Move ₹{gap_amt:,.0f} to long-term assets for growth."
    },

    "liquidity_ratio": 
    {
        "extremely_low": "Liquid assets cover only {user_value:.1f} months of expenses. Boost this by at least ₹{gap_amt:,.0f} to handle emergencies effectively.",
        "low": "You have limited liquidity ({user_value:.1f} months). Add ₹{gap_amt:,.0f} more to reach the 3–4 month ideal range.",
        "high": "Your liquidity ratio is higher than needed. Redirect ₹{gap_amt:,.0f} to equity or debt investments to optimize returns.",
        "extremely_high": "You’re holding too much in low-return liquid assets. Shift ₹{gap_amt:,.0f} to more productive investments."
    },

    "asset_liability_ratio": 
    {
        "extremely_low": "Your liabilities greatly exceed your assets (ratio: {user_value:.2f}). Focus on clearing debts or building assets worth ₹{gap_amt:,.0f}.",
        "low": "Your asset-liability ratio is below safe levels. Increase net worth by ₹{gap_amt:,.0f} through debt repayment or asset growth.",
        "high": "Your assets substantially exceed liabilities, which is great. Maintain or reallocate ₹{gap_amt:,.0f} for goal-based planning.",
        "extremely_high": "Your asset base is very strong. Consider putting ₹{gap_amt:,.0f} to work through goal-aligned investments."
    },

    "housing_income_ratio": 
    {
        "extremely_low": "You're spending just {user_value:.0%} on housing. Ensure you're not compromising on safety or convenience.",
        "low": "Housing expenses are modest at {user_value:.0%}. That’s efficient—consider whether lifestyle upgrades worth ₹{gap_amt:,.0f} are justified.",
        "high": "Housing takes up {user_value:.0%} of your income. Reduce rent or EMIs by ₹{gap_amt:,.0f} if possible.",
        "extremely_high": "At {user_value:.0%}, housing is consuming too much. Consider downsizing or refinancing to free up ₹{gap_amt:,.0f} monthly."
    },

    "health_insurance_adequacy": 
    {
        "extremely_low": "Your health cover of ₹{user_value:,.0f} is dangerously insufficient. Raise it by ₹{gap_amt:,.0f} to protect against medical risks.",
        "low": "You may be underinsured with only ₹{user_value:,.0f}. Increase coverage by ₹{gap_amt:,.0f} to meet basic protection standards.",
        "high": "Your health insurance is slightly higher than typical needs. You may review it to optimize ₹{gap_amt:,.0f} in premium savings.",
        "extremely_high": "You're overinsured in health with ₹{user_value:,.0f}. Consider trimming ₹{gap_amt:,.0f} in coverage to reduce costs."
    },

    "term_insurance_adequacy": 
    {
        "extremely_low": "You have zero or negligible term insurance (₹{user_value:,.0f}). Secure your family by adding at least ₹{gap_amt:,.0f} in coverage.",
        "low": "Your term cover of ₹{user_value:,.0f} may fall short. Increase it by ₹{gap_amt:,.0f} to align with 20× income rule.",
        "high": "You have slightly more term cover than required. Assess if ₹{gap_amt:,.0f} can be optimized to reduce premiums.",
        "extremely_high": "Term insurance of ₹{user_value:,.0f} may be excessive. Reduce ₹{gap_amt:,.0f} to save on premiums."
    },

    "retirement_adequacy": 
    {
        "extremely_low": "Your retirement savings are only {user_value:.0%} of the target. Begin investing at least ₹{gap_amt:,.0f}/month to secure your future.",
        "low": "You're behind on retirement readiness ({user_value:.0%}). Raise monthly contributions by ₹{gap_amt:,.0f} to catch up.",
        "high": "You're ahead on retirement ({user_value:.0%}). Reassess goals—extra savings of ₹{gap_amt:,.0f} can support early retirement or legacy planning.",
        "extremely_high": "You’ve oversaved for retirement at {user_value:.0%}. You might ease contributions by ₹{gap_amt:,.0f} and focus on current goals."
    },

    "net_worth_adequacy": 
    {
        "extremely_low": "Your net worth is critically low at current age. Accelerate asset creation by at least ₹{gap_amt:,.0f} annually.",
        "low": "Your net worth is below expected benchmarks. Build additional assets worth ₹{gap_amt:,.0f} to stay financially resilient.",
        "high": "Your net worth is higher than peers. Consider using ₹{gap_amt:,.0f} to explore higher-return or impact-driven opportunities.",
        "extremely_high": "You’re well ahead in net worth growth. Use this advantage to reduce working years or build legacy plans with ₹{gap_amt:,.0f}."
    }
}
