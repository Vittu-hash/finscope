"""Rule engine package for FinScope financial calculations"""

from .allocation import compute_allocation
from .analyzer import analyze_expenses
from .insights import generate_insights

__all__ = ['compute_allocation', 'analyze_expenses', 'generate_insights']
