"""
Test Configuration Profiles for Character Perturbation Robustness Test Suite

This module defines pre-configured test profiles for different scenarios:
  - FULL: Comprehensive testing across all languages and sources
  - QUICK: Fast iteration testing (subset of languages)
  - MINIMAL: Minimal testing (single language, single source)
  - DEEP: In-depth testing with advanced analysis
  - PER_LANGUAGE: Separate test profile for each language

Usage in Python:
    from test_config import TEST_PROFILES
    config = TEST_PROFILES['QUICK']
    
    python test_character_perturbation_robustness.py \\
        --languages {' '.join(config['languages'])} \\
        --sources {' '.join(config['sources'])} \\
        --output-dir {config['output_dir_name']}

Usage in Bash:
    source test_config.sh
    run_test_profile "QUICK"
"""

# ============================================================================
# PYTHON CONFIGURATION
# ============================================================================

TEST_PROFILES = {
    "FULL": {
        "description": "Comprehensive test suite for all languages and sources",
        "languages": ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"],
        "sources": ["ePark", "ILRDF_Dicts", "Paiwan_Stories", "NTUFormosanCorpus"],
        "test_ratio": 0.2,
        "laplace_smoothing": True,
        "expected_duration_minutes": 30,
        "estimated_output_size_mb": 50,
        "notes": "Full suite tests all 7 languages with all 4 sources. Requires ~30 min."
    },
    
    "QUICK": {
        "description": "Fast test with subset of languages for iteration",
        "languages": ["ami", "pwn"],
        "sources": ["ePark", "ILRDF_Dicts"],
        "test_ratio": 0.2,
        "laplace_smoothing": True,
        "expected_duration_minutes": 3,
        "estimated_output_size_mb": 5,
        "notes": "Tests 2 languages (well-resourced, distinct typology). ~3 minutes."
    },
    
    "MINIMAL": {
        "description": "Minimal test for validation",
        "languages": ["ami"],
        "sources": ["ePark"],
        "test_ratio": 0.2,
        "laplace_smoothing": True,
        "expected_duration_minutes": 1,
        "estimated_output_size_mb": 1,
        "notes": "Single language, single source. ~1 minute. For quick validation."
    },
    
    "DEEP": {
        "description": "In-depth analysis with multiple metrics and bootstrap resampling",
        "languages": ["ami", "pwn", "tay"],
        "sources": ["ePark", "ILRDF_Dicts", "Paiwan_Stories"],
        "test_ratio": 0.2,
        "laplace_smoothing": True,
        "bootstrap_iterations": 10,  # Custom field for future extension
        "compute_confidence_intervals": True,  # Custom field for future extension
        "expected_duration_minutes": 20,
        "estimated_output_size_mb": 25,
        "notes": "Deeper analysis with more iterations. Tests 3 languages with 3 sources."
    },
    
    "UNDER_RESOURCED": {
        "description": "Focus on under-resourced languages",
        "languages": ["dru", "pyu", "tay"],
        "sources": ["ILRDF_Dicts", "NTUFormosanCorpus"],
        "test_ratio": 0.2,
        "laplace_smoothing": True,
        "expected_duration_minutes": 10,
        "estimated_output_size_mb": 10,
        "notes": "Tests 3 under-resourced languages. Useful for assessing data scarcity impact."
    },
    
    "CROSS_VALIDATION": {
        "description": "Cross-validation across different corpus splits",
        "languages": ["ami", "pwn"],
        "sources": ["ePark", "ILRDF_Dicts", "Paiwan_Stories"],
        "test_ratio": 0.3,  # Different ratio for cross-validation
        "laplace_smoothing": True,
        "expected_duration_minutes": 8,
        "estimated_output_size_mb": 8,
        "notes": "Uses 30% test ratio instead of 20% for different evaluation split."
    },
}

# Per-language profiles for individual testing
LANGUAGE_PROFILES = {
    "ami": {
        "description": "Amis language robustness profile",
        "sources": ["ePark", "ILRDF_Dicts", "NTUFormosanCorpus"],
        "expected_dialects": ["Central", "Nataoran"],
    },
    "pwn": {
        "description": "Paiwan language robustness profile",
        "sources": ["Paiwan_Stories", "ILRDF_Dicts", "NTUFormosanCorpus"],
        "expected_dialects": ["Central", "Rukai"],
    },
    "tay": {
        "description": "Atayal language robustness profile",
        "sources": ["ILRDF_Dicts", "NTUFormosanCorpus"],
        "expected_dialects": ["Squliq", "S'uli", "C'uli"],
    },
    "bnn": {
        "description": "Bunun language robustness profile",
        "sources": ["ILRDF_Dicts", "NTUFormosanCorpus"],
        "expected_dialects": ["Takbanuaz", "Daabu", "Isbukun"],
    },
    "trv": {
        "description": "Seediq/Taroko language robustness profile",
        "sources": ["ILRDF_Dicts", "NTUFormosanCorpus"],
        "expected_dialects": ["Truku", "Toda"],
    },
    "dru": {
        "description": "Rukai language robustness profile",
        "sources": ["ILRDF_Dicts"],
        "expected_dialects": ["Tanan"],
    },
    "pyu": {
        "description": "Puyuma language robustness profile",
        "sources": ["ILRDF_Dicts"],
        "expected_dialects": ["Katipul"],
    },
}

# Perturbation strategies (for future extension)
PERTURBATION_STRATEGIES = {
    "most_frequent": {
        "description": "Swap most frequent character (current default)",
        "priority": 1,
        "notes": "Produces largest impact on distributions"
    },
    "least_frequent": {
        "description": "Swap least frequent character",
        "priority": 2,
        "notes": "Tests impact of rare character perturbation"
    },
    "random": {
        "description": "Swap random character",
        "priority": 3,
        "notes": "Average-case perturbation impact"
    },
    "vowel_swap": {
        "description": "Swap high-frequency vowel",
        "priority": 4,
        "notes": "Language-specific strategy"
    },
    "consonant_swap": {
        "description": "Swap high-frequency consonant",
        "priority": 5,
        "notes": "Language-specific strategy"
    },
}

# Metric configurations
METRIC_CONFIGS = {
    "default": {
        "description": "Standard metrics (Cosine Similarity, KL Divergence)",
        "metrics": ["cosine_similarity", "kl_divergence"],
        "levels": ["character", "word"],
        "n_grams": [1, 2, 3],
        "laplace_smoothing": True,
    },
    "extended": {
        "description": "Extended metrics including Jaccard, Overlap, Euclidean",
        "metrics": [
            "jaccard_similarity",
            "overlap_coefficient",
            "cosine_similarity",
            "euclidean_distance",
            "kl_divergence"
        ],
        "levels": ["character", "word"],
        "n_grams": [1, 2, 3],
        "laplace_smoothing": True,
    },
    "minimal": {
        "description": "Minimal metrics for fast iteration",
        "metrics": ["cosine_similarity"],
        "levels": ["character"],
        "n_grams": [1],
        "laplace_smoothing": True,
    },
}

# Result analysis configurations
ANALYSIS_CONFIGS = {
    "basic": {
        "description": "Basic result aggregation and summary",
        "compute_stats": ["mean", "std", "min", "max"],
        "group_by": ["language", "dialect", "gram_length"],
    },
    "detailed": {
        "description": "Detailed statistical analysis",
        "compute_stats": ["mean", "std", "min", "max", "median", "quartiles"],
        "group_by": ["language", "dialect", "gram_length", "metric"],
        "compute_correlations": True,
    },
    "publication": {
        "description": "Publication-ready analysis with confidence intervals",
        "compute_stats": ["mean", "std", "ci_95", "se"],
        "group_by": ["language", "dialect", "metric"],
        "compute_effect_sizes": True,
        "format_for_latex": True,
    },
}

# Predefined test scenarios
TEST_SCENARIOS = {
    "validation": {
        "description": "Validate test suite functionality",
        "profile": "MINIMAL",
        "expected_files": ["all_results.json", "summary_report.txt"],
        "expected_results_count": 1,
    },
    "language_comparison": {
        "description": "Compare robustness across 7 languages",
        "profile": "FULL",
        "expected_files": ["all_results.json", "comparative_analysis.txt"],
        "expected_results_count": 14,  # ~2 dialects per language average
    },
    "resource_impact": {
        "description": "Assess impact of corpus size on robustness",
        "profile": "UNDER_RESOURCED",
        "analysis_config": "detailed",
        "expected_results_count": 8,
    },
    "iteration": {
        "description": "Fast iteration during development",
        "profile": "QUICK",
        "expected_duration_minutes": 5,
    },
}


def get_profile(profile_name):
    """Retrieve a test profile by name."""
    if profile_name not in TEST_PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(TEST_PROFILES.keys())}")
    return TEST_PROFILES[profile_name]


def get_language_profile(lang_code):
    """Retrieve a language-specific profile by code."""
    if lang_code not in LANGUAGE_PROFILES:
        raise ValueError(f"Unknown language: {lang_code}. Available: {list(LANGUAGE_PROFILES.keys())}")
    return LANGUAGE_PROFILES[lang_code]


def get_scenario(scenario_name):
    """Retrieve a predefined test scenario by name."""
    if scenario_name not in TEST_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(TEST_SCENARIOS.keys())}")
    return TEST_SCENARIOS[scenario_name]


def print_profiles():
    """Print all available profiles in human-readable format."""
    print("\n" + "=" * 80)
    print("AVAILABLE TEST PROFILES")
    print("=" * 80)
    
    for name, config in TEST_PROFILES.items():
        print(f"\n{name.upper()}")
        print("-" * 80)
        print(f"  Description: {config['description']}")
        print(f"  Languages ({len(config['languages'])}): {', '.join(config['languages'])}")
        print(f"  Sources ({len(config['sources'])}): {', '.join(config['sources'])}")
        print(f"  Test Ratio: {config['test_ratio']}")
        print(f"  Expected Duration: ~{config['expected_duration_minutes']} minutes")
        print(f"  Estimated Output: ~{config['estimated_output_size_mb']} MB")
        print(f"  Notes: {config['notes']}")


def print_scenarios():
    """Print all available test scenarios in human-readable format."""
    print("\n" + "=" * 80)
    print("AVAILABLE TEST SCENARIOS")
    print("=" * 80)
    
    for name, scenario in TEST_SCENARIOS.items():
        print(f"\n{name.upper()}")
        print("-" * 80)
        print(f"  Description: {scenario['description']}")
        print(f"  Profile: {scenario['profile']}")
        if 'expected_duration_minutes' in scenario:
            print(f"  Expected Duration: ~{scenario['expected_duration_minutes']} minutes")
        if 'expected_results_count' in scenario:
            print(f"  Expected Results: {scenario['expected_results_count']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--profiles":
            print_profiles()
        elif sys.argv[1] == "--scenarios":
            print_scenarios()
        else:
            profile_name = sys.argv[1]
            if profile_name in TEST_PROFILES:
                import json
                print(json.dumps(TEST_PROFILES[profile_name], indent=2))
            else:
                print(f"Unknown profile: {profile_name}")
                sys.exit(1)
    else:
        print_profiles()
        print()
        print_scenarios()
