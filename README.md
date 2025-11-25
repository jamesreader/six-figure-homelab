# Homelab Learning Journey

## Goal
Build skills in DevOps, Security Engineering, and Data Engineering over six months to transition to a six-figure technical role.

## Hardware
* **Hyper-V host:** 128GB RAM, 8 cores (Windows desktop)
* **3x Ubuntu Server 24.04 VMs:**
  - homelab1 (192.168.2.30) - k3s control plane
  - homelab2 (192.168.2.32) - k3s worker
  - homelab3 (192.168.2.33) - k3s worker
* **12TB NAS storage** (arriving soon)
* **Network:** Home LAN (192.168.2.x/24) via Synology router
* **OPNsense VM** configured for future network segmentation

## Current Status: Week 5-6 (Ahead of Schedule)

### Completed Projects

#### Multi-Container Dashboard Application
**Location:** `docker-dashboard/`
- Three-tier application (nginx + Flask + PostgreSQL)
- Docker Compose orchestration
- GitHub Actions CI/CD pipeline
- Automated builds to Docker Hub

#### Kubernetes Cluster Deployment
**Location:** `kubernetes/dashboard/`
- 3-node k3s cluster with multi-node orchestration
- Ingress routing with Traefik (http://dashboard.homelab)
- High availability testing (automatic pod rescheduling on node failure)
- Persistent storage for PostgreSQL
- 6 replicas each of frontend/backend distributed across cluster

### Skills Demonstrated
✅ Linux system administration (SSH, networking, user management)  
✅ Docker fundamentals (containers, volumes, networks, custom images)  
✅ Container orchestration (docker-compose, Kubernetes)  
✅ Infrastructure as code (YAML manifests, declarative configuration)  
✅ CI/CD pipelines (GitHub Actions, automated builds)  
✅ Networking (ingress controllers, service discovery, DNS)  
✅ Troubleshooting distributed systems  
✅ Git/GitHub workflow with professional documentation  

## Progress Tracker
Interactive web app: http://192.168.2.30/roadmap-tracker.html

## Repository Structure
```
homelab/
├── docker-dashboard/          # Multi-container web application
│   ├── frontend/              # nginx + HTML/JS
│   ├── backend/               # Flask REST API
│   └── docker-compose.yml     # Orchestration config
├── kubernetes/                # K8s manifests and configs
│   └── dashboard/             # Dashboard deployment
│       ├── namespace.yaml
│       ├── postgres-*.yaml
│       ├── backend-deployment.yaml
│       ├── frontend-deployment.yaml
│       ├── ingress.yaml
│       └── README.md
└── roadmap-tracker/           # Progress tracking web app
```

## Quick Start

### Access Dashboard
Add to hosts file:
```
192.168.2.30    dashboard.homelab
```
Visit: http://dashboard.homelab

### Manage Kubernetes Cluster
```bash
# View cluster status
kubectl get nodes
kubectl get pods -n dashboard -o wide

# Scale applications
kubectl scale deployment backend -n dashboard --replicas=9

# Test node failure
ssh jreader@homelab2 'sudo shutdown -h now'
kubectl get pods -n dashboard -o wide -w
```

## Next Steps
- **Week 7-8:** SQL & Databases (practice queries, design schemas, build portfolio tracker)
- **Week 11-12:** Infrastructure as Code (Terraform, Ansible)
- **Week 13-14:** Monitoring & Logging (Prometheus, Grafana, ELK stack)

## Learning Approach
- Hands-on, project-driven methodology
- Build portfolio-worthy projects, not tutorials
- Document everything in GitHub
- Focus on skills that translate directly to job interviews

---

**Note:** Network isolation with OPNsense remains configured but not implemented. Current focus is on building orchestration and automation skills over infrastructure complexity.
