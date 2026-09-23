#!/usr/bin/env python3
"""gigmath - true hourly pay for gig work, in one file. Python stdlib only.

Turns a gig's real numbers (payout, miles, minutes, fees) into the hourly
rate that actually reaches your pocket after platform fees, fuel, and
vehicle wear. Counts unpaid deadhead miles and wait minutes, the two
costs that quietly wreck gig math.

Examples:
  python3 gigmath.py --fare 14.75 --tip 3 --miles 12 --minutes 41 --fee-pct 12
  python3 gigmath.py --fare 14.75 --tip 3 --miles 12 --minutes 41 --fee-pct 12 --wait 14 --deadhead 12 --gas-price 3.15 --mpg 31
  python3 gigmath.py --fare 14.75 --tip 3 --miles 12 --minutes 41 --json
"""
import argparse
import json
import sys


def money(x):
    return "${:,.2f}".format(x)


def build():
    p = argparse.ArgumentParser(description="true hourly pay for gig work")
    p.add_argument("--fare", type=float, required=True, help="gross fare for the gig")
    p.add_argument("--tip", type=float, default=0.0, help="tip amount")
    p.add_argument("--promo", type=float, default=0.0, help="promo/quest bonus")
    p.add_argument("--fee-pct", type=float, default=0.0, help="platform fee, %% of fare")
    p.add_argument("--miles", type=float, required=True, help="paid trip miles")
    p.add_argument("--deadhead", type=float, default=0.0, help="unpaid return miles")
    p.add_argument("--minutes", type=float, required=True, help="drive minutes")
    p.add_argument("--wait", type=float, default=0.0, help="unpaid wait minutes")
    p.add_argument("--gas-price", type=float, default=3.10, help="fuel price per gallon")
    p.add_argument("--mpg", type=float, default=30.0, help="vehicle miles per gallon")
    p.add_argument("--wear", type=float, default=0.07, help="wear cost per mile")
    p.add_argument("--target", type=float, default=15.0, help="minimum acceptable hourly")
    p.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    return p.parse_args()


def main():
    a = build()
    errs = []
    if a.fare < 0 or a.tip < 0 or a.promo < 0:
        errs.append("money inputs cannot be negative")
    if a.miles < 0 or a.deadhead < 0 or a.minutes < 0 or a.wait < 0:
        errs.append("distance and time inputs cannot be negative")
    if a.mpg <= 0:
        errs.append("--mpg must be positive")
    if a.fee_pct < 0 or a.fee_pct > 100:
        errs.append("--fee-pct must be 0-100")
    if errs:
        for e in errs:
            print("error:", e, file=sys.stderr)
        sys.exit(2)
    total_min = a.minutes + a.wait
    if total_min <= 0:
        print("error: total time is zero, hourly rate undefined", file=sys.stderr)
        sys.exit(2)

    gross = a.fare + a.tip + a.promo
    fee = a.fare * a.fee_pct / 100.0
    tm = a.miles + a.deadhead
    fuel = tm / a.mpg * a.gas_price
    wear_cost = tm * a.wear
    net = gross - fee - fuel - wear_cost
    hours = total_min / 60.0
    hourly = net / hours
    verdict = "at or above target" if hourly >= a.target else "below target"

    if a.as_json:
        print(json.dumps({
            "gross": round(gross, 2), "fees": round(fee, 2),
            "total_miles": round(tm, 1), "fuel_cost": round(fuel, 2),
            "wear_cost": round(wear_cost, 2), "net": round(net, 2),
            "minutes": total_min, "hourly": round(hourly, 2),
            "target": a.target, "verdict": verdict,
        }))
        sys.exit(0 if hourly >= a.target else 1)

    print("Gross payout:      " + money(gross).rjust(10))
    print("Platform fee:      " + money(fee).rjust(10) + "  ({}% of fare)".format(a.fee_pct))
    print("Fuel ({} mi):".format(round(tm, 1)).ljust(19) + money(fuel).rjust(10))
    print("Wear ({} mi):".format(round(tm, 1)).ljust(19) + money(wear_cost).rjust(10))
    print("Net take:          " + money(net).rjust(10))
    print("Time on the clock: " + (str(round(total_min)) + " min").rjust(10))
    print("TRUE HOURLY:       " + (money(hourly) + "/hr").rjust(10) + "  " + verdict)
    sys.exit(0 if hourly >= a.target else 1)


if __name__ == "__main__":
    main()
