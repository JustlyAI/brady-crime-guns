#!/usr/bin/env python3
"""
Federal Civil Procedure Deadline Calculator
Calculates litigation deadlines considering weekends, federal holidays, and service methods.
"""

import argparse
from datetime import datetime, timedelta
import json
import sys

# Federal holidays (observance dates may vary)
FEDERAL_HOLIDAYS = {
    2024: [
        "2024-01-01",  # New Year's Day
        "2024-01-15",  # MLK Day
        "2024-02-19",  # Presidents Day
        "2024-05-27",  # Memorial Day
        "2024-06-19",  # Juneteenth
        "2024-07-04",  # Independence Day
        "2024-09-02",  # Labor Day
        "2024-10-14",  # Columbus Day
        "2024-11-11",  # Veterans Day
        "2024-11-28",  # Thanksgiving
        "2024-12-25",  # Christmas
    ],
    2025: [
        "2025-01-01",  # New Year's Day
        "2025-01-20",  # MLK Day
        "2025-02-17",  # Presidents Day
        "2025-05-26",  # Memorial Day
        "2025-06-19",  # Juneteenth
        "2025-07-04",  # Independence Day
        "2025-09-01",  # Labor Day
        "2025-10-13",  # Columbus Day
        "2025-11-11",  # Veterans Day
        "2025-11-27",  # Thanksgiving
        "2025-12-25",  # Christmas
    ]
}

# Common deadline periods in federal civil procedure
DEADLINE_RULES = {
    "answer": {
        "standard": 21,
        "waiver_domestic": 60,
        "waiver_foreign": 90,
        "description": "Time to answer complaint (FRCP 12(a))"
    },
    "motion_to_dismiss": {
        "standard": 21,
        "description": "Time to file Rule 12(b) motion"
    },
    "reply": {
        "standard": 21,
        "description": "Time to reply to counterclaim (FRCP 12(a)(1)(B))"
    },
    "discovery_response": {
        "standard": 30,
        "description": "Time to respond to discovery requests (FRCP 33, 34, 36)"
    },
    "summary_judgment": {
        "standard": 30,
        "after_close_discovery": 30,
        "description": "Time limits for summary judgment (FRCP 56)"
    },
    "appeal": {
        "civil": 30,
        "government_party": 60,
        "description": "Time to file notice of appeal (FRAP 4(a))"
    },
    "motion_response": {
        "standard": 14,
        "description": "Time to respond to motion (varies by local rule)"
    },
    "motion_reply": {
        "standard": 7,
        "description": "Time to file reply brief (varies by local rule)"
    }
}

def is_federal_holiday(date):
    """Check if a date is a federal holiday"""
    date_str = date.strftime("%Y-%m-%d")
    year = date.year
    
    if year in FEDERAL_HOLIDAYS:
        return date_str in FEDERAL_HOLIDAYS[year]
    return False

def is_weekend(date):
    """Check if a date is a weekend"""
    return date.weekday() in [5, 6]  # Saturday = 5, Sunday = 6

def is_business_day(date):
    """Check if a date is a business day (not weekend or federal holiday)"""
    return not is_weekend(date) and not is_federal_holiday(date)

def add_days(start_date, days, count_type="calendar"):
    """
    Add days to a date, with options for different counting methods
    
    Args:
        start_date: Starting date
        days: Number of days to add
        count_type: "calendar" or "business"
    """
    if count_type == "calendar":
        result = start_date + timedelta(days=days)
    else:  # business days
        result = start_date
        days_added = 0
        while days_added < days:
            result += timedelta(days=1)
            if is_business_day(result):
                days_added += 1
    
    return result

def extend_to_business_day(date):
    """If date falls on weekend/holiday, extend to next business day per FRCP 6(a)"""
    while not is_business_day(date):
        date += timedelta(days=1)
    return date

def add_service_days(date, service_method):
    """Add additional days based on service method per FRCP 6(d)"""
    additional_days = {
        "electronic": 0,
        "hand": 0,
        "mail": 3,
        "overnight": 0,
        "other_means": 3
    }
    
    days_to_add = additional_days.get(service_method, 0)
    return add_days(date, days_to_add, "calendar")

def calculate_deadline(event_date, rule_type, service_method="electronic", waiver=False, foreign=False):
    """
    Calculate a deadline based on federal civil procedure rules
    
    Args:
        event_date: The triggering event date
        rule_type: Type of deadline (from DEADLINE_RULES)
        service_method: Method of service
        waiver: Whether service was waived (for answer deadlines)
        foreign: Whether party is foreign (for waived service)
    """
    if rule_type not in DEADLINE_RULES:
        raise ValueError(f"Unknown rule type: {rule_type}")
    
    rule = DEADLINE_RULES[rule_type]
    
    # Determine base period
    if rule_type == "answer" and waiver:
        if foreign:
            days = rule["waiver_foreign"]
        else:
            days = rule["waiver_domestic"]
    else:
        days = rule["standard"]
    
    # Calculate raw deadline
    deadline = add_days(event_date, days, "calendar")
    
    # Add service days if applicable (not for initial complaints)
    if rule_type not in ["answer", "appeal"]:
        deadline = add_service_days(deadline, service_method)
    
    # Extend to business day if needed (FRCP 6(a))
    final_deadline = extend_to_business_day(deadline)
    
    return {
        "event_date": event_date.strftime("%Y-%m-%d"),
        "rule_type": rule_type,
        "rule_description": rule["description"],
        "base_days": days,
        "service_method": service_method,
        "raw_deadline": deadline.strftime("%Y-%m-%d"),
        "final_deadline": final_deadline.strftime("%Y-%m-%d"),
        "is_extended": deadline != final_deadline,
        "days_until": (final_deadline - datetime.now().date()).days
    }

def main():
    parser = argparse.ArgumentParser(description="Calculate federal civil procedure deadlines")
    parser.add_argument("--event_date",
                       help="Triggering event date (YYYY-MM-DD). Defaults to today's date if not specified.")
    parser.add_argument("--rule_type", required=True,
                       choices=list(DEADLINE_RULES.keys()),
                       help="Type of deadline to calculate")
    parser.add_argument("--service_method", default="electronic",
                       choices=["electronic", "hand", "mail", "overnight", "other_means"],
                       help="Method of service")
    parser.add_argument("--waiver", action="store_true",
                       help="Service was waived (for answer deadlines)")
    parser.add_argument("--foreign", action="store_true",
                       help="Party is foreign (for waived service)")
    parser.add_argument("--jurisdiction", default="federal",
                       help="Jurisdiction (currently only federal supported)")

    args = parser.parse_args()

    try:
        # Parse event date - default to today if not specified
        if args.event_date:
            event_date = datetime.strptime(args.event_date, "%Y-%m-%d").date()
        else:
            event_date = datetime.now().date()
        
        # Calculate deadline
        result = calculate_deadline(
            event_date=event_date,
            rule_type=args.rule_type,
            service_method=args.service_method,
            waiver=args.waiver,
            foreign=args.foreign
        )
        
        # Output result
        print(json.dumps(result, indent=2))
        
        # Also print human-readable summary
        print(f"\n📅 DEADLINE CALCULATION SUMMARY")
        print(f"{'='*40}")
        print(f"Event Date: {result['event_date']}")
        print(f"Rule: {result['rule_description']}")
        print(f"Base Period: {result['base_days']} days")
        print(f"Service Method: {result['service_method']}")
        print(f"Raw Deadline: {result['raw_deadline']}")
        if result['is_extended']:
            print(f"⚠️  Extended to: {result['final_deadline']} (weekend/holiday)")
        else:
            print(f"Final Deadline: {result['final_deadline']}")
        
        if result['days_until'] < 0:
            print(f"⛔ DEADLINE PASSED {abs(result['days_until'])} days ago!")
        elif result['days_until'] == 0:
            print(f"⚠️  DEADLINE IS TODAY!")
        elif result['days_until'] <= 7:
            print(f"⚠️  {result['days_until']} days remaining!")
        else:
            print(f"✅ {result['days_until']} days remaining")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()