"""Insights module - generates actionable financial insights"""

def generate_insights(allocation: dict, analysis: dict, expenses: dict) -> list:
    """
    Generate insights based on allocation and expense analysis.
    
    Args:
        allocation: Recommended allocation from allocation.py
        analysis: Analysis results from analyzer.py
        expenses: Actual expense dict
    
    Returns:
        List of insight strings
    """
    insights = []
    
    recommended_savings = allocation["amounts"]["savings"]
    actual_savings = expenses.get("savings", 0)
    
    # Savings gap
    if actual_savings < recommended_savings:
        gap = recommended_savings - actual_savings
        insights.append(f"You're saving ₹{gap:.2f} less than recommended. Try to increase your savings to ₹{recommended_savings:.2f}/month.")
    elif actual_savings > recommended_savings:
        insights.append(f"Great job! You're saving ₹{actual_savings - recommended_savings:.2f} more than recommended.")
    
    # Emergency fund gap
    recommended_emergency = allocation["amounts"]["emergency"]
    insights.append(f"Maintain an emergency fund of at least ₹{recommended_emergency:.2f}/month for unexpected expenses.")
    
    # Check overspending categories
    comparison = analysis["comparison"]
    for category, data in comparison.items():
        if category == "savings":
            continue
            
        # Flag if spending >10% of salary on entertainment or shopping
        if category in ["entertainment", "shopping"] and data["percentOfSalary"] > 10:
            insights.append(f"{category.capitalize()} spending is {data['percentOfSalary']:.1f}% of salary. Consider reducing to below 10%.")
        
        # Flag any category overspending by >50%
        if data["delta"] > 0 and data["recommended"] > 0:
            overspend_pct = (data["delta"] / data["recommended"]) * 100
            if overspend_pct > 50:
                insights.append(f"You're overspending on {category} by ₹{data['delta']:.2f} ({overspend_pct:.0f}% above recommended).")
    
    # Total expenses check
    total_actual = analysis["actualSummary"]["totalActualSpending"]
    salary = allocation["salary"]
    total_recommended = salary * 0.85  # 85% is reasonable for all expenses
    
    if total_actual > total_recommended:
        insights.append(f"Your total expenses (₹{total_actual:.2f}) exceed recommended spending (₹{total_recommended:.2f}). Look for areas to cut back.")
    
    # If no major issues
    if len(insights) == 0 or (len(insights) == 1 and "emergency" in insights[0].lower()):
        insights.append("Your spending looks healthy! Keep monitoring your expenses regularly.")
    
    return insights
