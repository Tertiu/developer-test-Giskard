import argparse
import os
from kernel import lib
parser = argparse.ArgumentParser()
parser.add_argument("falcon_file", help="path to millennium-falcon.json", type=str)
parser.add_argument("empire_file", help="path to empire.json", type=str)
args = parser.parse_args()

assert os.path.isfile(args.falcon_file), "Invalid Falcon File"
assert os.path.isfile(args.empire_file), "Invalid Empire File"

falcon = lib.read_json(args.falcon_file)
falcon["routes_db"] = lib.repair_path(args.falcon_file, falcon["routes_db"])
assert os.path.isfile(falcon["routes_db"]), "Invalid Falcon DB File"
routes = lib.processDB(falcon["routes_db"])
(countdown, hunters_planning) = lib.processEmpire(args.empire_file)
result = lib.process_a_star(routes, falcon["departure"], falcon["arrival"], falcon["autonomy"], countdown, hunters_planning)    
if result is None:
    print("0")
else:
    fail_odds = lib.compute_proba(result[0])
    print("{:.2g}".format((1 - fail_odds)*100))
