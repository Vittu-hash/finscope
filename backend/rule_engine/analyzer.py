"""Analyzer module - analyzes actual expenses vs recommended limits"""

def analyze_expenses(salary: float, expenses: dict) -> dict:
    """
    Analyze actual expenses against recommended category limits.
    
    Args:
        salary: Monthly salary
        expenses: Dict of expense categories and amounts
    
    Returns:
        dict with actual summary, recommended values, and comparison
    """
    # Recommended category limits as % of salary
    recommended_pct = {
        "groceries": 10,
        "rent": 30,
        "utilities": 5,
        "travel": 7,
        "entertainment": 5,
        "shopping": 5,
        "health": 5,
        "education": 3,
        "savings": 10,
        "other": 5
    }
    
    # Calculate recommended amounts
    recommended_amounts = {
        category: round((pct / 100) * salary, 2)
        for category, pct in recommended_pct.items()
    }
    
    # Calculate actual totals
    total_actual = sum(expenses.values())
    pct_of_salary = round((total_actual / salary) * 100, 2) if salary > 0 else 0
    
    # Build comparison
    comparison = {}
    for category in recommended_pct.keys():
        actual = expenses.get(category, 0)
        recommended = recommended_amounts[category]
        delta = round(actual - recommended, 2)
        pct = round((actual / salary) * 100, 2) if salary > 0 else 0
        
        comparison[category] = {
            "actual": actual,
            "recommended": recommended,
            "delta": delta,
            "percentOfSalary": pct
        }
    
    return {
        "actualSummary": {
            "categories": expenses,
            "totalActualSpending": total_actual,
            "pctOfSalary": pct_of_salary,
            "recommendedValues": recommended_amounts
        },
        "comparison": comparison
    }
