from typing import Dict

REVIEW_AREAS: Dict[str, Dict[str, Dict[str, str]]] = {
    "savings_income_ratio": {
        "high": {
            "current_scenario": (
                "Your savings‑to‑income ratio is {user_value:.1f}, which is above the typical range of "
                "[{min_val}, {max_val}]. Please review this to ensure the excess savings aren’t impacting "
                "other financial needs."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your savings‑to‑income ratio is a striking {user_value:.1f}, well beyond the expected "
                "range [{min_val}, {max_val}]. If this is unintentional, it may be holding you back from a better lifestyle."
            )
        },
    },
    "investment_income_ratio": {
        "high": {
            "current_scenario": (
                "Your investment‑income ratio stands at {user_value:.1f}, which exceeds the normal ranges of "
                "[{min_val}, {max_val}]. It may be worth reviewing your portfolio allocation."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your investment‑income ratio is an unusually high {user_value:.1f}, far above the typical levels of "
                "[{min_val}, {max_val}]. Double‑check if this aligns with your risk and liquidity goals."
            )
        },
    },
    # "expense_income_ratio": {
    #     "high": {
    #         "current_scenario": (
    #             "Your expense‑to‑income ratio is {user_value:.1f}, exceeding the recommended maximum of "
    #             "{max_val}. Please review your budget to confirm this is intentional."
    #         )
    #     },
    #     "extremely_high": {
    #         "current_scenario": (
    #             "Your expense‑to‑income ratio is a concerning {user_value:.1f}, well above "
    #             "{max_val}. Evaluate whether this level of expenditure is sustainable."
    #         )
    #     },
    # },
    # "debt_income_ratio": {
    #     "high": {
    #         "current_scenario": (
    #             "Your debt‑to‑income ratio is {user_value:.1f}, which is higher than the advised ceiling of "
    #             "{max_val}. You may want to review your debt obligations."
    #         )
    #     },
    #     "extremely_high": {
    #         "current_scenario": (
    #             "Your debt‑to‑income ratio is an alarmingly high {user_value:.1f}, exceeding "
    #             "{max_val} by a large margin. Consider reviewing your repayment strategy."
    #         )
    #     },
    # },
    "emergency_fund_ratio": {
        "high": {
            "current_scenario": (
                "Your emergency‑fund ratio is {user_value:.1f} months, above the suggested upper limit of "
                "{max_val} months. Verify if this level of reserves is purposeful."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your emergency‑fund ratio at {user_value:.1f} months far exceeds the guideline "
                "[{min_val}, {max_val}] months. High liquidity levels may be better off invested, unless otherwise intended."
            )
        },
    },
    "liquidity_ratio": {
        "high": {
            "current_scenario": (
                "Your liquidity ratio is {user_value:.1f} months, which is above the typical band of "
                "[{min_val}, {max_val}] months. Please review to ensure you’re not holding too much in cash."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your liquidity ratio at {user_value:.1f} months is significantly beyond the general "
                "[{min_val}, {max_val}] month range. You may want to shift it if its sitting idle."
            )
        },
    },
    "asset_liability_ratio": {
        "high": {
            "current_scenario": (
               "Your asset‑to‑liability ratio is {user_value:.2f}, past the typical maximum of {max_val}, indicating you have a solid net‑asset buffer. If you wish to amplify your portfolio’s growth, you could consider borrowing against your holdings—but be sure to review the associated risks and align it with your financial goals."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your asset‑to‑liability ratio is exceptionally high at {user_value:.2f}, well above the expected maximum of {max_val}, reflecting a large pool of unleveraged assets. If you’re comfortable with additional risk and have a clear investment plan, you may leverage your position to pursue higher returns; otherwise, you’re already in a very strong position."
            )
        },
    },
    # "housing_income_ratio": {
    #     "high": {
    #         "current_scenario": (
    #             "Your housing‑income ratio is {user_value:.1f}, which exceeds the recommended maximum of "
    #             "{max_val}. You might want to review your housing costs."
    #         )
    #     },
    #     "extremely_high": {
    #         "current_scenario": (
    #             "Your housing‑income ratio at {user_value:.1f} is well above "
    #             "{max_val}. We recommend downsizing."
    #         )
    #     },
    # },
    "health_insurance_adequacy": {
        "high": {
            "current_scenario": (
                "Your health‑insurance adequacy score is {user_value:.1f}, above the expected range "
                "[{min_val}, {max_val}]. Please review to ensure you’re not over‑insured."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your health‑insurance adequacy of {user_value:.1f} is significantly above "
                "[{min_val}, {max_val}]. Verify this level of coverage is intentional."
            )
        },
    },
    "term_insurance_adequacy": {
        "high": {
            "current_scenario": (
                "Your term‑insurance adequacy score is {user_value:.1f}, higher than the usual max of "
                "{max_val}. You may wish to review your policy limits."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your term‑insurance adequacy at {user_value:.1f} greatly exceeds "
                "{max_val}. Ensure this policy size is deliberate."
            )
        },
    },
    "net_worth_adequacy": {
        "high": {
            "current_scenario": (
                "Your net‑worth adequacy ratio is {user_value:.2f}, above the normal band of "
                "[{min_val}, {max_val}]. You might want to confirm your asset valuations."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your net‑worth adequacy of {user_value:.2f} far exceeds "
                "[{min_val}, {max_val}]. Check for anomalies or intentional overvaluation."
            )
        },
    },
    "retirement_adequacy": {
        "high": {
            "current_scenario": (
                "Your retirement‑adequacy is {user_value:.1f}, above the typical target range of "
                "[{min_val}, {max_val}]. Impressive readiness, although ensure it's not at the expense of current lifestyle."
            )
        },
        "extremely_high": {
            "current_scenario": (
                "Your retirement‑adequacy of {user_value:.1f} is well beyond "
                "[{min_val}, {max_val}]. If you wish, pause investments for retirement to fund your current ambitions."
            )
        },
    },
}
