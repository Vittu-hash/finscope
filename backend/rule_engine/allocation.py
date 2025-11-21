"""Allocation module - computes risk-based allocation percentages and amounts"""

def compute_allocation(salary: float, age: int, risk_level: str) -> dict:
    """
    Compute recommended allocation based on salary, age, and risk level.
    
    Returns:
        dict with percentages and amounts for expenses, savings, investments, emergency
    """
    # Base risk allocations
    risk_profiles = {
        "Low": {"expenses": 50, "savings": 25, "investments": 15, "emergency": 10},
        "Medium": {"expenses": 50, "savings": 20, "investments": 25, "emergency": 5},
        "High": {"expenses": 45, "savings": 15, "investments": 35, "emergency": 5}
    }
    
    # Get base allocation
    base = risk_profiles.get(risk_level, risk_profiles["Medium"])
    
    # Age adjustments
    age_adjustment = 0
    if 18 <= age <= 24:
        age_adjustment = {"investments": +3, "emergency": -3}
    elif 25 <= age <= 34:
        age_adjustment = {"investments": +2, "emergency": -2}
    elif 35 <= age <= 44:
        age_adjustment = {"investments": 0, "emergency": 0}
    elif 45 <= age <= 54:
        age_adjustment = {"investments": -2, "emergency": +2}
    elif age >= 55:
        age_adjustment = {"investments": -4, "emergency": +4}
    else:
        age_adjustment = {"investments": 0, "emergency": 0}
    
    # Apply adjustments
    percentages = {
        "expenses": base["expenses"],
        "savings": base["savings"],
        "investments": base["investments"] + age_adjustment.get("investments", 0),
        "emergency": base["emergency"] + age_adjustment.get("emergency", 0)
    }
    
    # Ensure total is 100
    total = sum(percentages.values())
    if total != 100:
        diff = 100 - total
        percentages["expenses"] += diff
    
    # Calculate amounts
    amounts = {
        key: round((pct / 100) * salary, 2)
        for key, pct in percentages.items()
    }
    
    return {
        "percentages": percentages,
        "amounts": amounts,
        "salary": salary
    }
