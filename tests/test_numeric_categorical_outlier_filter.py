import pandas as pd
from app.services.recommendation_engine import generate_business_recommendations


def _rules(df):
    return {item['rule_id'] for item in generate_business_recommendations(df, [])}


def test_cardio_binary_and_ordinal_columns_are_not_flagged_as_iqr_outliers():
    # Reproduces the relevant structure of cardio_train: numeric codes are
    # categorical even though pandas stores them as integers.
    n = 1000
    df = pd.DataFrame({
        'active': [0] * 500 + [1] * 500,
        'smoke': [0] * 950 + [1] * 50,
        'gluc': ([1] * 700) + ([2] * 200) + ([3] * 100),
        'cholesterol': ([1] * 650) + ([2] * 250) + ([3] * 100),
    })
    rules = _rules(df)
    assert not any(rule.startswith('numerical_outliers:') for rule in rules)


def test_continuous_measurements_still_receive_iqr_screening():
    df = pd.DataFrame({'sales': [100, 102, 98, 101, 99, 103, 97, 100, 101, 1000]})
    rules = _rules(df)
    assert 'numerical_outliers:sales' in rules


def test_binary_column_is_not_flagged_even_if_imbalanced():
    df = pd.DataFrame({'active': [0] * 990 + [1] * 10})
    rules = _rules(df)
    assert 'numerical_outliers:active' not in rules


def test_small_cardinality_unlabelled_integer_code_is_excluded():
    df = pd.DataFrame({'response_code': [1] * 80 + [2] * 10 + [3] * 10})
    rules = _rules(df)
    assert 'numerical_outliers:response_code' not in rules
