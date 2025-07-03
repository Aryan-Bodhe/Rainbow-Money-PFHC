HEADER_TEMPLATES = {
    'ratio_headers': {
        'bad': [
            "High {metric_name}",
            "Low {metric_name}",
            "{metric_name} Critically Low",
            "Excessive {metric_name}",
        ],
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
