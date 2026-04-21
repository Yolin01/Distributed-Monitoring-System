"""
Génère un token longue durée pour un agent.
Usage : python scripts/generate_agent_token.py --node agent-01 --role operator
"""
import argparse, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datetime import timedelta
from src.server.app.security import create_access_token

parser = argparse.ArgumentParser()
parser.add_argument("--node", required=True)
parser.add_argument("--role", default="operator")
parser.add_argument("--days", type=int, default=365)
args = parser.parse_args()

token = create_access_token(
    {"sub": args.node, "role": args.role},
    expires_delta=timedelta(days=args.days)
)
print(f"\nToken pour '{args.node}' ({args.role}, {args.days}j):\n")
print(token)