HEADER_TEMPLATES = {
    "ratio_headers": {
        "bad": {
            "high": [
                "High {metric_name}",
                "Excessive {metric_name}",
                "Above normal {metric_name}",
                "Higher than ideal {metric_name}"
            ],
            "low": [
                "Low {metric_name}",
                "{metric_name} very low",
                "Below average {metric_name}",
                "Lower than ideal {metric_name}"
            ]
        },
        'good': [
            "Good {metric_name}",
            "Optimal {metric_name}",
            "Strong {metric_name}",
            "Healthy {metric_name}"
        ]
    },
    'adequacy_headers': {
        'bad': [
            "Inadequate {metric_name}",
            "Insufficient {metric_name}",
        ],
        'good': [
            "Good {metric_name}",
            "Strong {metric_name}",
            "Stable {metric_name}"
        ]
    },
    'asset_allocation_headers': {
        'bad': [
            "Overexposed to {metric_name}",
            "Underexposed to {metric_name}"
        ],
        'good': [
            "Rebalance {metric_name}",
            "Diversify {metric_name}"
        ]
    }
}
