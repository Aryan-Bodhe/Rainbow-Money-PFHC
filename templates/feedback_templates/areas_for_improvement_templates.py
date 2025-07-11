AREAS_FOR_IMPROVEMENT = {
    "emergency_fund_ratio": {
        "extremely_low": {
            "current_scenario": "Your emergency fund covers only {user_value:.1f} months, which is dangerously low.",
            "actionable": "Build at least ₹{gap_amt:,.0f} to reach the minimum recommended {min_val} months of expenses."
        },
        "low": {
            "current_scenario": "You have {user_value:.1f} months of emergency savings.",
            "actionable": "Increase it by ₹{gap_amt:,.0f} to meet the minimum target of {min_val} months."
        },
        "high": {
            "current_scenario": "Your emergency fund covers {user_value:.1f} months—more than required.",
            "actionable": "Consider shifting ₹{gap_amt:,.0f} to investments to stay within the ideal range of {min_val}–{max_val} months."
        },
        "extremely_high": {
            "current_scenario": "You’ve overfunded your emergency reserves at {user_value:.1f} months.",
            "actionable": "Move ₹{gap_amt:,.0f} to long-term assets to align with the target range of {min_val}–{max_val} months."
        },
    },

    "liquidity_ratio": {
        "extremely_low": {
            "current_scenario": "Liquid assets cover only {user_value:.1f} months of expenses.",
            "actionable": "Boost this by ₹{gap_amt:,.0f} to reach at least {min_val} months of coverage."
        },
        "low": {
            "current_scenario": "You have limited liquidity at {user_value:.1f} months.",
            "actionable": "Add ₹{gap_amt:,.0f} to reach the recommended range of {min_val}–{max_val} months."
        },
        "high": {
            "current_scenario": "Your liquidity ratio is higher than needed at {user_value:.1f} months.",
            "actionable": "Redirect ₹{gap_amt:,.0f} to productive investments to stay within {min_val}–{max_val}."
        },
        "extremely_high": {
            "current_scenario": "You’re holding too much in low-return liquid assets ({user_value:.1f} months).",
            "actionable": "Shift ₹{gap_amt:,.0f} into growth investments to optimize your allocation."
        },
    },

    "asset_liability_ratio": {
        "extremely_low": {
            "current_scenario": "Your liabilities greatly exceed your assets (ratio: {user_value:.2f}).",
            "actionable": "Build assets or repay debts worth ₹{gap_amt:,.0f} to achieve at least a {min_val} ratio."
        },
        "low": {
            "current_scenario": "Your asset-liability ratio is below safe levels at {user_value:.2f}.",
            "actionable": "Improve it by ₹{gap_amt:,.0f} through debt reduction or asset growth."
        },
        "high": {
            "current_scenario": "Your assets substantially exceed liabilities (ratio: {user_value:.2f}).",
            "actionable": "Maintain or reallocate ₹{gap_amt:,.0f} for better goal-aligned efficiency."
        },
        "extremely_high": {
            "current_scenario": "You have a very strong asset base (ratio: {user_value:.2f}).",
            "actionable": "Consider putting ₹{gap_amt:,.0f} to work through long-term planning."
        },
    },

    "housing_income_ratio": {
        "extremely_low": {
            "current_scenario": "You're spending just {user_value:.0%} on housing.",
            "actionable": "Ensure this isn’t at the cost of comfort or safety; review if a modest lifestyle upgrade within {max_val:.0%} is feasible."
        },
        "low": {
            "current_scenario": "Your housing expenses are modest at {user_value:.0%}.",
            "actionable": "If desired, improve quality of life with upgrades, staying within {max_val:.0%} of income."
        },
        "high": {
            "current_scenario": "Housing takes up {user_value:.0%} of your income.",
            "actionable": "Try to reduce housing costs by ₹{gap_amt:,.0f} to fall within the {min_val:.0%}–{max_val:.0%} recommended range."
        },
        "extremely_high": {
            "current_scenario": "At {user_value:.0%}, housing is consuming too much of your income.",
            "actionable": "Consider downsizing or restructuring loans to bring it below {max_val:.0%}."
        },
    },

    "health_insurance_adequacy": {
        "extremely_low": {
            "current_scenario": "Your health cover of ₹{user_value:,.0f} is insufficient given your family size.",
            "actionable": "Increase it by ₹{gap_amt:,.0f} to meet the minimum requirement of ₹{min_val:,.0f}."
        },
        "low": {
            "current_scenario": "You may be underinsured with only ₹{user_value:,.0f} of health cover.",
            "actionable": "Add ₹{gap_amt:,.0f} to align with the benchmark minimum of ₹{min_val:,.0f}."
        },
        "high": {
            "current_scenario": "Your health insurance exceeds the expected level at ₹{user_value:,.0f}.",
            "actionable": "You could review coverage and save up to ₹{gap_amt:,.0f} in premiums."
        },
        "extremely_high": {
            "current_scenario": "You’re overinsured with health coverage of ₹{user_value:,.0f}.",
            "actionable": "Trim down to save ₹{gap_amt:,.0f} annually while staying within the ideal ₹{max_val:,.0f}."
        },
    },

    "term_insurance_adequacy": {
        "extremely_low": {
            "current_scenario": "Your term insurance of ₹{user_value:,.0f} is very low, leaving loved ones underprotected.",
            "actionable": "Secure your family by adding at least ₹{gap_amt:,.0f} to reach ₹{min_val:,.0f} coverage."
        },
        "low": {
            "current_scenario": "Your term cover of ₹{user_value:,.0f} is below optimal levels.",
            "actionable": "Increase it by ₹{gap_amt:,.0f} to align with the ₹{min_val:,.0f}–₹{max_val:,.0f} guideline."
        },
        "high": {
            "current_scenario": "You have more term cover than required (₹{user_value:,.0f}).",
            "actionable": "Reassess if ₹{gap_amt:,.0f} in premiums can be optimized."
        },
        "extremely_high": {
            "current_scenario": "Term insurance of ₹{user_value:,.0f} may be excessive.",
            "actionable": "Consider reducing coverage by ₹{gap_amt:,.0f} to stay efficient."
        },
    },

    "retirement_adequacy": {
        "extremely_low": {
            "current_scenario": "Your retirement savings are only {user_value:.0%} of the required amount.",
            "actionable": "Start investing at least ₹{gap_amt:,.0f}/month to reach {min_val:.0%} adequacy."
        },
        "low": {
            "current_scenario": "You're behind on retirement readiness at {user_value:.0%}.",
            "actionable": "Boost contributions by ₹{gap_amt:,.0f} to target the {min_val:.0%}–{max_val:.0%} range."
        },
        "high": {
            "current_scenario": "You're ahead on retirement with {user_value:.0%} adequacy.",
            "actionable": "You may redirect ₹{gap_amt:,.0f} toward short-term goals while staying above {min_val:.0%}."
        },
        "extremely_high": {
            "current_scenario": "You’ve oversaved for retirement at {user_value:.0%}.",
            "actionable": "Ease contributions by ₹{gap_amt:,.0f} if current priorities need more focus."
        },
    },

    "net_worth_adequacy": {
        "extremely_low": {
            "current_scenario": "Your net worth is critically low for your age group.",
            "actionable": "Accelerate asset creation or reduce high-value debts (if any)."
        },
        "low": {
            "current_scenario": "Your net worth is below expected benchmarks.",
            "actionable": "Build additional assets to move towards a healthy range."
        },
        "high": {
            "current_scenario": "You’ve accumulated strong net worth for your age.",
            "actionable": "Explore advanced goals or impact opportunities with the surplus."
        },
        "extremely_high": {
            "current_scenario": "You are significantly ahead in wealth accumulation.",
            "actionable": "Use the excess assets for legacy planning or lifestyle flexibility."
        },
    },

    "savings_income_ratio": {
        "extremely_low": {
            "current_scenario": "Your savings rate is only {user_value:.0%} of income—far below healthy levels.",
            "actionable": "Increase monthly savings by ₹{gap_amt:,.0f} to reach at least {min_val:.0%} of your income."
        },
        "low": {
            "current_scenario": "You’re saving {user_value:.0%} of your income.",
            "actionable": "Aim to boost savings by ₹{gap_amt:,3.0f} to enter the ideal {min_val:.0%}–{max_val:.0%} band."
        },
        "high": {
            "current_scenario": "Your savings rate is {user_value:.0%}, slightly above target.",
            "actionable": "You may consider reallocating ₹{gap_amt:,.0f} toward debt repayment or investments."
        },
        "extremely_high": {
            "current_scenario": "You’re saving {user_value:.0%} of income–perhaps too much.",
            "actionable": "Ensure that you balance savings with lifestyle; consider utilising ₹{gap_amt:,.0f} for personal goals, investing, or debt reduction."
        },
    },

    "investment_income_ratio": {
        "extremely_low": {
            "current_scenario": "Only {user_value:.0%} of income is going into investments—very low.",
            "actionable": "Allocate an extra ₹{gap_amt:,.0f} monthly to investments to hit {min_val:.0%}."
        },
        "low": {
            "current_scenario": "Your investment rate is {user_value:.0%}.",
            "actionable": "Increase by ₹{gap_amt:,.0f} to get within the {min_val:.0%}–{max_val:.0%} range."
        },
        "high": {
            "current_scenario": "Investments make up {user_value:.0%} of your income—above the target.",
            "actionable": "Consider diverting ₹{gap_amt:,.0f} towards other goals like emergency funds."
        },
        "extremely_high": {
            "current_scenario": "You’re investing {user_value:.0%} of income—excellent but aggressive.",
            "actionable": "Review liquidity to ensure you’re not overexposed; free up ₹{gap_amt:,.0f} if needed."
        },
    },

    "expense_income_ratio": {
        "extremely_low": {
            "current_scenario": "Your expenses are only {user_value:.0%} of income—unusually low.",
            "actionable": "Review if essential needs are met; you could allocate ₹{gap_amt:,.0f} toward better quality of life."
        },
        "low": {
            "current_scenario": "You spend {user_value:.0%} of your income.",
            "actionable": "If comfortable, consider increasing to {min_val:.0%}–{max_val:.0%} for balanced living."
        },
        "high": {
            "current_scenario": "Expenses are {user_value:.0%} of income—above ideal.",
            "actionable": "Cut down monthly expenses by ₹{gap_amt:,.0f} to reach {max_val:.0%}."
        },
        "extremely_high": {
            "current_scenario": "You’re spending {user_value:.0%} of income—very high.",
            "actionable": "Implement a budget cut of ₹{gap_amt:,.0f} to curb spending into {max_val:.0%} territory."
        },
    },

    "debt_income_ratio": {
        "extremely_low": {
            "current_scenario": "Your debt is {user_value:.0%} of income—almost zero, which is excellent.",
            "actionable": "You may consider safe debt leverage for growth, if appropriate."
        },
        "low": {
            "current_scenario": "Debt stands at {user_value:.0%} of income.",
            "actionable": "It’s healthy and reduces financial strain–keep it up!."
        },
        "high": {
            "current_scenario": "Your debt is {user_value:.0%} of income—above target.",
            "actionable": "Consider repaying debts as soon as possible to fall within the {min_val:.0%}–{max_val:.0%} guideline."
        },
        "extremely_high": {
            "current_scenario": "Debt at {user_value:.0%} of income is very high.",
            "actionable": "Focus on repaying high-value debts urgently using snowballing technique to reduce financial strain."
        },
    },
}
