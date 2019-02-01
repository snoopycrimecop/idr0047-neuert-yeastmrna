import sys
import yaml

with open(sys.argv[1], 'r') as f:
    data = yaml.load(f)


with open(sys.argv[1], 'w') as f:
    yaml.dump(
        data, f, width=80, explicit_start=True,
        indent=2, default_flow_style=False)
