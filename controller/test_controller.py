"""
Test script for the Controller module.
Run: python -m controller.test_controller
"""

from controller import calculate_priority, allocate_budget
from controller.scheduler import AdaptiveScheduler, run_collection_cycle


def test_priority_calculation():
    """Test the priority formula."""
    print("=" * 50)
    print("TEST 1: Priority Calculation")
    print("=" * 50)
    
    # Test cases
    sources = [
        {"name": "High Quality", "avg_utility": 0.9, "avg_noise": 0.1, "avg_cost": 1.0},
        {"name": "Medium Quality", "avg_utility": 0.5, "avg_noise": 0.3, "avg_cost": 1.0},
        {"name": "Low Quality", "avg_utility": 0.3, "avg_noise": 0.6, "avg_cost": 1.0},
        {"name": "Cheap & Good", "avg_utility": 0.7, "avg_noise": 0.2, "avg_cost": 0.5},
    ]
    
    print("\nFormula: score = (utility / cost) * (1 - noise * 1.5)\n")
    
    for source in sources:
        score = calculate_priority(source)
        print(f"  {source['name']:15} → Score: {score:.3f}")
        print(f"    utility={source['avg_utility']}, noise={source['avg_noise']}, cost={source['avg_cost']}")
    
    print("\n✅ Higher score = Better source")


def test_budget_allocation():
    """Test budget allocation (uses database)."""
    print("\n" + "=" * 50)
    print("TEST 2: Budget Allocation (from database)")
    print("=" * 50)
    
    try:
        sources = allocate_budget(total_calls=10)
        
        if not sources:
            print("\n⚠️  No sources found in database.")
            print("   Run: python -m database.seed_data first")
            return
        
        print(f"\nTotal budget: 10 API calls\n")
        
        total_allocated = 0
        for s in sources:
            print(f"  {s['name']:25} → {s['allocated_calls']} calls (score: {s['priority_score']:.3f})")
            total_allocated += s['allocated_calls']
        
        print(f"\n  Total allocated: {total_allocated} calls")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure database is configured (.env)")


def test_collection_plan():
    """Test the full collection plan."""
    print("\n" + "=" * 50)
    print("TEST 3: Collection Plan (full cycle)")
    print("=" * 50)
    
    try:
        plan = run_collection_cycle(total_budget=10)
        
        print(f"\nTimestamp: {plan['timestamp']}")
        print(f"Total budget: {plan['total_budget']}")
        print(f"Stale sources: {plan['stale_count']}")
        print("\nCollection order:")
        
        for i, s in enumerate(plan['sources'], 1):
            stale = "🔴 STALE" if s['is_stale'] else "🟢 Fresh"
            print(f"  {i}. {s['name']:25} → {s['allocated_calls']} calls | {stale}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure database is configured (.env)")


if __name__ == "__main__":
    print("\n🧪 CONTROLLER MODULE TESTS\n")
    
    test_priority_calculation()
    test_budget_allocation()
    test_collection_plan()
    
    print("\n" + "=" * 50)
    print("✨ Tests complete!")
    print("=" * 50 + "\n")
