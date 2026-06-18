#!/usr/bin/env python3
"""
=============================================================================
custom_dynamic_inventory.py
-----------------------------------------------------------------------------
PURPOSE:
This script is an EXAMPLE of how dynamic inventory worked BEFORE inventory
PLUGINS existed (and still works today). This is how engineers used to
write dynamic inventory: as a standalone SCRIPT that prints JSON.

HOW DOES ANSIBLE TALK TO A SCRIPT-BASED INVENTORY?
Ansible can call ANY executable script as inventory, as long as it:
  1. Responds to "--list"
     → prints ALL groups, hosts, and host variables as JSON
  2. Responds to "--host <hostname>"
     → prints variables for ONE specific host as JSON

WHY LEARN THIS IF THE "amazon.aws.aws_ec2" PLUGIN ALREADY EXISTS?
  - It helps you understand EXACTLY what "dynamic inventory" means under
    the hood — it's just a program that returns JSON.
  - You can build CUSTOM inventories from ANY data source: a database,
    an internal CMDB/asset tracker, a spreadsheet, another cloud provider,
    or even multiple sources combined.
  - Some older Ansible setups still rely on script-based inventories.

HOW TO USE THIS SCRIPT:
  # 1. Make it executable
  chmod +x custom_dynamic_inventory.py

  # 2. Test it manually — should print JSON with all your running instances
  ./custom_dynamic_inventory.py --list

  # 3. Test a single host
  ./custom_dynamic_inventory.py --host 54.12.34.56

  # 4. Use it with Ansible directly
  ansible-playbook -i custom_dynamic_inventory.py playbook.yml
=============================================================================
"""

import json       # Used to convert Python dictionaries into JSON text
import sys        # Used to read command-line arguments (--list, --host)
import boto3      # AWS SDK for Python — lets us talk to AWS EC2


def get_ec2_instances():
    """
    -------------------------------------------------------------------
    Connects to AWS and fetches every EC2 instance that is currently
    RUNNING. Returns a simple Python list, where each item is a
    dictionary describing ONE instance.
    -------------------------------------------------------------------
    """

    # Create a connection ("client") to the EC2 service.
    # Change region_name below if your servers live in a different region.
    ec2 = boto3.client("ec2", region_name="us-east-1")

    # Ask AWS: "give me all instances where state = running"
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    instances = []  # This list will hold the info we extract for each server

    # AWS groups instances inside "Reservations" — loop through each one
    for reservation in response["Reservations"]:

        # Each reservation can contain MULTIPLE instances — loop through those too
        for instance in reservation["Instances"]:

            # Try to find the "Name" tag (e.g. "web-server-1").
            # If the instance has no Name tag, default to "unnamed".
            name = "unnamed"
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]

            # Build a small dictionary containing only the fields we need.
            # .get() is used for optional fields so the script doesn't crash
            # if an instance has no public IP (e.g. it's in a private subnet).
            instances.append({
                "id": instance["InstanceId"],                       # e.g. "i-0abc123def456"
                "name": name,                                        # e.g. "web-server-1"
                "public_ip": instance.get("PublicIpAddress", ""),    # e.g. "54.12.34.56"
                "private_ip": instance.get("PrivateIpAddress", ""),  # e.g. "10.0.0.5"
                "instance_type": instance["InstanceType"],           # e.g. "t2.micro"
            })

    return instances


def build_inventory():
    """
    -------------------------------------------------------------------
    Builds the FULL inventory dictionary that Ansible expects when you
    run this script with "--list".

    The required structure is:
    {
        "all": {
            "hosts": [list of hostnames/IPs],
            "vars": {variables shared by ALL hosts}
        },
        "_meta": {
            "hostvars": {
                "host1": {variables specific to host1},
                "host2": {variables specific to host2}
            }
        }
    }
    -------------------------------------------------------------------
    """

    instances = get_ec2_instances()

    all_hosts = []   # Will hold the IP address of every server we find
    hostvars = {}    # Will hold connection details for EACH server

    for instance in instances:

        # We use the PUBLIC IP as the "name" Ansible will use for this host.
        # If an instance has no public IP, we skip it in this simple example
        # (Ansible running from your laptop can't reach a private-only IP).
        host = instance["public_ip"]
        if not host:
            continue

        all_hosts.append(host)

        # Define the variables Ansible needs to connect to THIS specific host.
        hostvars[host] = {
            "ansible_host": instance["public_ip"],

            # Custom facts about this instance — useful inside playbooks
            "instance_id": instance["id"],
            "instance_name": instance["name"],
            "instance_type": instance["instance_type"],
            "private_ip": instance["private_ip"],

            # SSH connection details — EDIT THESE to match your setup:
            "ansible_user": "ubuntu",                       # default user for Ubuntu AMIs
            "ansible_ssh_private_key_file": "~/.ssh/id_rsa" # path to your private key
        }

    # Assemble the final inventory structure Ansible expects
    inventory = {
        "all": {
            "hosts": all_hosts,
            "vars": {}
        },
        "_meta": {
            "hostvars": hostvars
        }
    }

    return inventory


def get_host_vars(hostname):
    """
    -------------------------------------------------------------------
    Called when Ansible runs this script with "--host <hostname>".
    Returns ONLY the variables for that ONE specific host.
    -------------------------------------------------------------------
    """
    inventory = build_inventory()
    return inventory["_meta"]["hostvars"].get(hostname, {})


# =============================================================================
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
# When Ansible runs this script, it passes either "--list" or
# "--host <hostname>" as a command-line argument. We check which one
# was given and print the correct JSON response.
# =============================================================================
if __name__ == "__main__":

    if len(sys.argv) >= 2 and sys.argv[1] == "--list":
        # Print the FULL inventory (every group, host, and hostvar) as JSON
        print(json.dumps(build_inventory(), indent=2))

    elif len(sys.argv) >= 3 and sys.argv[1] == "--host":
        # Print variables for ONE host only, as JSON
        print(json.dumps(get_host_vars(sys.argv[2]), indent=2))

    else:
        # If the script was called incorrectly, show usage and exit with
        # a non-zero status code to indicate an error
        print("Usage: custom_dynamic_inventory.py --list | --host <hostname>")
        sys.exit(1)
