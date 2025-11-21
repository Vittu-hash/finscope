import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent.parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

tips_data = [
    {
        "id": "tip1",
        "dailyTip": "Track your daily expenses to stay within budget.",
        "microLessons": [
            "Start with the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
            "Build an emergency fund covering 3-6 months of expenses.",
            "Invest early to benefit from compound interest."
        ]
    },
    {
        "id": "tip2",
        "dailyTip": "Review your subscriptions monthly to eliminate unused services.",
        "microLessons": [
            "Cancel subscriptions you haven't used in 30 days.",
            "Look for annual plans that offer better value.",
            "Set reminders before free trials end."
        ]
    },
    {
        "id": "tip3",
        "dailyTip": "Automate your savings to ensure consistent wealth building.",
        "microLessons": [
            "Set up automatic transfers to savings on payday.",
            "Use apps that round up purchases and save the difference.",
            "Increase savings rate by 1% every quarter."
        ]
    },
    {
        "id": "tip4",
        "dailyTip": "Compare prices before making major purchases.",
        "microLessons": [
            "Wait 24 hours before buying non-essential items over ₹5000.",
            "Use price comparison websites and apps.",
            "Check for cashback and reward opportunities."
        ]
    },
    {
        "id": "tip5",
        "dailyTip": "Maintain a separate emergency fund for unexpected expenses.",
        "microLessons": [
            "Keep emergency funds in a high-yield savings account.",
            "Only use emergency funds for true emergencies.",
            "Replenish the fund immediately after use."
        ]
    }
]

async def seed_tips():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing tips
    await db.tips.delete_many({})
    
    # Insert new tips
    await db.tips.insert_many(tips_data)
    
    print(f"Successfully seeded {len(tips_data)} tips!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_tips())
