# 🌐 Ansible Dynamic Inventory — AWS EC2

A hands-on project demonstrating how to use **dynamic inventory** in Ansible
to automatically discover and manage AWS EC2 instances — no manually
maintained list of servers required.

---

## 📑 Table of Contents

- [What is Dynamic Inventory?](#what-is-dynamic-inventory)
- [Static vs Dynamic Inventory](#static-vs-dynamic-inventory)
- [How the AWS EC2 Plugin Works](#how-the-aws-ec2-plugin-works)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Configuration](#setup--configuration)
- [Usage](#usage)
- [Understanding the Output](#understanding-the-output)
- [Dynamic Groups Explained](#dynamic-groups-explained)
- [Custom Python Inventory Script](#custom-python-inventory-script)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## What is Dynamic Inventory?

In Ansible, an **inventory** is the list of servers (hosts) you want to manage.

A **static inventory** is a plain text file (`.ini` or `.yaml`) where you
manually type out every server's IP address or hostname. This works fine for
small, fixed environments — but breaks down in the cloud, where servers are
created and destroyed constantly (auto-scaling groups, ephemeral test
environments, etc.).

A **dynamic inventory** solves this by querying a live data source — in this
case, the AWS EC2 API — every time you run Ansible. Instead of a static list,
Ansible asks: *"What servers actually exist RIGHT NOW?"* and builds the
inventory on the fly.

---

## Static vs Dynamic Inventory

| | Static Inventory | Dynamic Inventory |
|---|---|---|
| **Format** | Plain `.ini` or `.yaml` file with hardcoded hosts | A config file or script that queries a live source (e.g. AWS) |
| **Maintenance** | Manual — must edit the file every time a server is added/removed | Automatic — always reflects the current state of your infrastructure |
| **Best for** | Small, fixed environments (e.g. a handful of on-prem servers) | Cloud environments with auto-scaling or frequently changing servers |
| **Example** | `[web]`<br>`192.168.1.10`<br>`192.168.1.11` | `plugin: amazon.aws.aws_ec2` (queries AWS live) |
| **Grouping** | Manual — you define groups yourself | Automatic — groups created from tags, instance type, region, etc. |

---

## How the AWS EC2 Plugin Works

This project uses the official **`amazon.aws.aws_ec2`** inventory plugin.
Here's the flow:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                  │
│   You run: ansible-playbook -i inventory/aws_ec2.yml playbook.yml │
│                          │                                       │
│                          ▼                                       │
│   Ansible reads inventory/aws_ec2.yml                            │
│                          │                                       │
│                          ▼                                       │
│   Plugin calls the AWS EC2 API (describe_instances)              │
│                          │                                       │
│                          ▼                                       │
│   AWS returns a live list of running instances                   │
│                          │                                       │
│                          ▼                                       │
│   Plugin builds inventory:                                        │
│     - Hosts   → public/private IPs                               │
│     - Groups  → based on tags, instance type, region              │
│     - Hostvars→ ansible_host, instance metadata                   │
│                          │                                       │
│                          ▼                                       │
│   Ansible connects to each host via SSH and runs the playbook    │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ansible-dynamic-inventory/
├── ansible.cfg                          # Ansible configuration — points to dynamic inventory
├── inventory/
│   ├── aws_ec2.yml                      # AWS EC2 dynamic inventory plugin config
│   └── custom_dynamic_inventory.py      # Educational: script-based inventory example
├── group_vars/
│   └── all.yml                          # Variables applied to ALL hosts (SSH user, key, etc.)
├── playbook.yml                         # Test playbook to verify dynamic inventory works
├── requirements.yml                     # Required Ansible collections (amazon.aws)
├── requirements.txt                     # Required Python packages (boto3, botocore)
└── README.md                            # This file
```

---

## Prerequisites

| Requirement | Purpose | Install |
|---|---|---|
| **Ansible** | Automation tool | `pip install ansible --break-system-packages` |
| **Python 3.8+** | Required by Ansible and boto3 | Pre-installed on most systems |
| **AWS CLI** | Authenticate with AWS | [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) |
| **AWS Account** | With at least one running EC2 instance | [aws.amazon.com](https://aws.amazon.com) |
| **SSH Key Pair** | To connect to your EC2 instances | `ssh-keygen -t rsa -b 4096` |

### Verify Installation

```bash
ansible --version
python3 --version
aws --version
```

---

## Setup & Configuration

### Step 1 — Configure AWS Credentials

The `aws_ec2` plugin uses the SAME credentials as the AWS CLI. Configure them with:

```bash
aws configure
```

```
AWS Access Key ID:      your-access-key-id
AWS Secret Access Key:  your-secret-access-key
Default region name:    us-east-1
Default output format:  json
```

> 💡 The plugin can also read credentials from environment variables:
> ```bash
> export AWS_ACCESS_KEY_ID="your-access-key-id"
> export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
> export AWS_REGION="us-east-1"
> ```

### Step 2 — Install Required Python Packages

```bash
pip install -r requirements.txt --break-system-packages
```

### Step 3 — Install Required Ansible Collections

```bash
ansible-galaxy collection install -r requirements.yml
```

### Step 4 — Update `group_vars/all.yml`

Open `group_vars/all.yml` and confirm the SSH user and private key path match
your EC2 setup:

```yaml
ansible_user: ubuntu                          # "ec2-user" for Amazon Linux
ansible_ssh_private_key_file: ~/.ssh/id_rsa   # Path to YOUR private key
```

### Step 5 — (Optional) Update Region or Filters

Open `inventory/aws_ec2.yml` and update the `regions` list if your instances
are not in `us-east-1`, or add tag-based filters if you only want to target
specific instances.

---

## Usage

### View the Dynamic Inventory

This command queries AWS and prints the full inventory **without** running
any playbook — useful for testing:

```bash
ansible-inventory -i inventory/aws_ec2.yml --list
```

Print the inventory as a readable tree of groups:

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
```

### Ping All Hosts

Quickly verify Ansible can connect to every running instance:

```bash
ansible all -i inventory/aws_ec2.yml -m ping
```

### Run the Test Playbook

```bash
ansible-playbook -i inventory/aws_ec2.yml playbook.yml
```

> 💡 If `ansible.cfg` is present in your working directory (as it is in this
> project), Ansible will automatically use `inventory/aws_ec2.yml` — so you
> can simply run:
> ```bash
> ansible-playbook playbook.yml
> ```

### Target a Specific Dynamic Group

Once you know which groups exist (see [Dynamic Groups Explained](#dynamic-groups-explained)),
you can target just one group:

```bash
# Target only t2.micro instances
ansible type_t2_micro -i inventory/aws_ec2.yml -m ping

# Target only instances tagged Environment=production
ansible tag_Environment_production -i inventory/aws_ec2.yml -m ping
```

---

## Understanding the Output

Running `ansible-inventory -i inventory/aws_ec2.yml --list` returns JSON
similar to this (simplified):

```json
{
  "_meta": {
    "hostvars": {
      "54.12.34.56": {
        "ansible_host": "54.12.34.56",
        "instance_id": "i-0abc123def456",
        "instance_type": "t2.micro",
        "placement": { "region": "us-east-1" },
        "tags": { "Name": "web-server-1", "Environment": "production" }
      }
    }
  },
  "all": {
    "children": ["ungrouped", "tag_Environment_production", "type_t2_micro", "aws_region_us_east_1"]
  },
  "tag_Environment_production": {
    "hosts": ["54.12.34.56"]
  },
  "type_t2_micro": {
    "hosts": ["54.12.34.56"]
  }
}
```

| Key | Meaning |
|---|---|
| `_meta.hostvars` | Variables for each individual host (IP, instance ID, tags, etc.) |
| `all.children` | All the groups that exist in this inventory |
| `tag_Environment_production` | A group automatically created from the `Environment: production` tag |
| `type_t2_micro` | A group automatically created from the instance type |

---

## Dynamic Groups Explained

The `keyed_groups` section in `inventory/aws_ec2.yml` automatically organizes
your EC2 instances into groups based on their metadata:

| Group Source | Example Tag/Attribute | Resulting Group Name |
|---|---|---|
| Instance Tags | `Environment: production` | `tag_Environment_production` |
| Instance Tags | `Team: devops` | `tag_Team_devops` |
| Instance Type | `t2.micro` | `type_t2_micro` |
| AWS Region | `us-east-1` | `aws_region_us_east_1` |

This means if you tag your EC2 instances well (e.g. `Environment`, `Role`,
`Team`), Ansible automatically organizes them for you — **no manual grouping
required**.

### Example: Targeting Groups in a Playbook

```yaml
- name: Configure only production web servers
  hosts: tag_Environment_production
  tasks:
    - name: Install Nginx
      ansible.builtin.apt:
        name: nginx
        state: present
```

---

## Custom Python Inventory Script

`inventory/custom_dynamic_inventory.py` is included for **educational
purposes** — it shows how dynamic inventory worked before plugins existed,
and how you could build a fully custom inventory from any data source
(a database, internal CMDB, multiple cloud providers, etc.).

### How It Works

Ansible calls the script with `--list` or `--host <ip>`, and the script
responds with JSON:

```bash
# Make it executable
chmod +x inventory/custom_dynamic_inventory.py

# Test it manually
./inventory/custom_dynamic_inventory.py --list

# Use it with Ansible
ansible-playbook -i inventory/custom_dynamic_inventory.py playbook.yml
```

> 💡 **In practice**, prefer the `amazon.aws.aws_ec2` plugin (used in this
> project) over custom scripts — it's officially maintained, supports
> caching, and handles pagination and error cases for you. The script is
> here purely to demonstrate the underlying concept.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `No inventory was parsed` | Plugin not enabled or collection not installed | Run `ansible-galaxy collection install -r requirements.yml` and check `enable_plugins` in `ansible.cfg` |
| `Unable to locate credentials` | AWS credentials not configured | Run `aws configure` or export `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |
| Empty inventory (`{}`) | No instances match the filters | Check `filters: instance-state-name: running` — ensure you have running instances |
| `Permission denied (publickey)` | Wrong SSH key or username | Verify `ansible_ssh_private_key_file` and `ansible_user` in `group_vars/all.yml` |
| `UNREACHABLE` on ping | Security group blocks SSH (port 22) | Ensure the EC2 security group allows inbound SSH from your IP |
| Groups not showing up | Instances missing tags | Add tags (e.g. `Environment: production`) to your EC2 instances in the AWS Console |
| Slow inventory queries | Large number of instances, no caching | Enable the `cache` settings in `inventory/aws_ec2.yml` |

---

## Security Notes

- **Never commit AWS credentials** to version control — use `aws configure`
  or environment variables, never hardcode keys in `.yml` files
- **Never commit your SSH private key** (`~/.ssh/id_rsa`) — add it to `.gitignore`
- The `amazon.aws` collection requires IAM permissions for `ec2:DescribeInstances`
  — grant only this read-only permission if the inventory user doesn't need to
  manage infrastructure
- `host_key_checking = False` in `ansible.cfg` is convenient for labs but
  reduces protection against man-in-the-middle attacks — re-enable it and
  manage `known_hosts` properly for production use

---

## Author

**ONEIL KIMBI**
Version: v1.0.0
