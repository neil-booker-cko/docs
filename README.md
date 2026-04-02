# Network Resilience Library

Technical documentation for sub-second failover and hybrid-cloud connectivity across
Cisco IOS-XE, Fortinet FortiGate, and AWS environments.

## Contents

| Section | Description |
| --- | --- |
| [Theory](docs/theory/) | Protocol convergence comparisons (BGP, OSPF, EIGRP vs BFD) |
| [Cisco](docs/cisco/) | BFD and failover guides for IOS-XE platforms |
| [FortiGate](docs/fortigate/) | BFD and failover guides for FortiOS appliances |
| [AWS Architecture](docs/aws/) | Hybrid cloud connectivity designs and troubleshooting |

## Local Preview

```bash
uv run mkdocs serve
```

Then open `http://127.0.0.1:8000`.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker, Traefik, CI/CD, and Watchtower setup.

---

*Created for Network Engineering Teams specializing in Hybrid Cloud Connectivity.*
