# Ansible Dynamic Inventory — AWS EC2

This project shows how to set up **dynamic inventory** in Ansible so it
automatically discovers your running AWS EC2 instances — no manual list
of servers needed.

## What is Dynamic Inventory?

Normally, Ansible needs a list of servers (an "inventory") to know what to
manage. A **static** inventory is a plain file where you type IPs by hand.
A **dynamic** inventory instead asks AWS, live, "what servers exist right
now?" — so the list is always accurate, even as servers are created or
destroyed.

## Project Files

```
ansible-dynamic-inventory-simple/
├── ansible.cfg              # Tells Ansible to use our dynamic inventory
├── inventory/
│   └── aws_ec2.yml          # Config for the AWS EC2 inventory plugin
├── group_vars/
│   └── all.yml              # SSH user/key settings applied to all hosts
├── playbook.yml             # Test playbook to confirm it all works
├── requirements.yml         # Ansible collection needed (amazon.aws)
└── requirements.txt         # Python packages needed (boto3)
```

## Step-by-Step Setup

### Step 1 — Install Ansible and Python dependencies

```bash
pip install ansible -r requirements.txt --break-system-packages
```

### Step 2 — Install the AWS collection

This gives Ansible the `aws_ec2` plugin used in `inventory/aws_ec2.yml`.

```bash
ansible-galaxy collection install -r requirements.yml
```

### Step 3 — Configure your AWS credentials

The inventory plugin uses the same credentials as the AWS CLI.

```bash
aws configure
```

Enter your Access Key, Secret Key, and region (e.g. `us-east-1`) when prompted.

### Step 4 — Set your SSH details

Open `group_vars/all.yml` and make sure the user and key path match your
EC2 setup:

```yaml
ansible_user: ubuntu
ansible_ssh_private_key_file: ~/.ssh/id_rsa
```

### Step 5 — Check the inventory works

Run this to see the live list of EC2 instances Ansible finds:

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
```

You should see your running instances grouped by tag and instance type.

### Step 6 — Test the connection

```bash
ansible all -i inventory/aws_ec2.yml -m ping
```

Each running instance should reply with `"pong"`.

### Step 7 — Run the test playbook

```bash
ansible-playbook playbook.yml
```

Since `ansible.cfg` already points to `inventory/aws_ec2.yml`, you don't
need to pass `-i` manually.

## How It All Connects

1. `ansible.cfg` tells Ansible to use `inventory/aws_ec2.yml` as the inventory
2. `inventory/aws_ec2.yml` asks AWS for all running EC2 instances and groups them by tag/type
3. `group_vars/all.yml` supplies the SSH username and key so Ansible can log into each instance
4. `playbook.yml` runs against every host the dynamic inventory found

## Common Issues

| Problem | Fix |
|---|---|
| `No inventory was parsed` | Run `ansible-galaxy collection install -r requirements.yml` |
| `Unable to locate credentials` | Run `aws configure` |
| `UNREACHABLE` when pinging | Check the EC2 security group allows SSH (port 22) |
| Empty inventory | Make sure you have at least one **running** EC2 instance |
