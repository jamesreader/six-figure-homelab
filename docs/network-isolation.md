# Network Isolation with OPNsense

## Overview

Implemented network segmentation in the homelab using OPNsense as a virtual firewall/router to isolate the Kubernetes cluster from the home network while maintaining controlled connectivity.

## Architecture

### Network Topology

```
Home Network (192.168.2.0/24)
├── Windows Host (192.168.2.222)
├── QNAP NAS (192.168.2.133)
└── OPNsense WAN Interface (192.168.2.100)
         |
         | (Firewall/Router)
         |
         └── OPNsense LAN Interface (10.0.0.1)
              |
              Isolated Lab Network (10.0.0.0/24)
              ├── homelab1 (10.0.0.x) - k3s control plane
              ├── homelab2 (10.0.0.x) - k3s worker
              └── homelab3 (10.0.0.x) - k3s worker
```

### Hyper-V Virtual Switch Configuration

- **EXTERNAL**: External virtual switch bridged to physical NIC
  - Home network access (192.168.2.0/24)
  - Connected to: OPNsense WAN, Windows host vNIC
  
- **LabLAN**: Internal virtual switch for isolated network
  - Isolated lab network (10.0.0.0/24)
  - Connected to: OPNsense LAN, all k3s nodes

## OPNsense Configuration

### Initial Setup

1. **VM Configuration** (Hyper-V)
   - Generation 2 VM
   - 2 Network Adapters:
     - Adapter 1 (WAN/hn1): Connected to EXTERNAL vSwitch
     - Adapter 2 (LAN/hn0): Connected to LabLAN vSwitch
   - Static IP configuration on both interfaces

2. **Interface Assignment**
   - WAN (hn1): 192.168.2.100/24
   - LAN (hn0): 10.0.0.1/24

3. **DHCP Configuration**
   - Enabled on LAN interface (10.0.0.0/24)
   - Automatically assigns IPs to k3s nodes

### Firewall Rules

#### WAN Interface Rules

**Allow Web UI Access from Home Network:**
- Action: Pass
- Interface: WAN
- Protocol: TCP
- Source: 192.168.2.0/24
- Destination: WAN address
- Destination Port: HTTPS (443)

**Allow ICMP (Ping):**
- Action: Pass
- Interface: WAN
- Protocol: ICMP
- Source: 192.168.2.0/24
- Destination: Any

**Allow Home Network to Access Isolated LAN:**
- Action: Pass
- Interface: WAN
- Protocol: Any
- Source: 192.168.2.0/24
- Destination: 10.0.0.0/24

**Critical Configuration:**
- Disabled "Block private networks" on WAN interface
  - Required because "WAN" is actually another RFC1918 private network
  - System → Interfaces → WAN → Uncheck "Block private networks"

#### LAN Interface Rules

- Default allow all outbound traffic from isolated network

### DNS Configuration with Unbound

#### Enable Unbound DNS

**Services → Unbound DNS → General**
- Enable Unbound DNS: ✓
- Listen Port: 53
- Network Interfaces: All

#### Host Overrides for Homelab

**Services → Unbound DNS → Overrides → Host Overrides**

Added custom DNS entries:
- `homelab1.homelab` → 10.0.0.x (k3s control plane)
- `homelab2.homelab` → 10.0.0.x (k3s worker)
- `homelab3.homelab` → 10.0.0.x (k3s worker)
- `dashboard.homelab` → 10.0.0.x (Traefik ingress)

#### DNS Forwarding

Unbound automatically forwards public DNS queries to upstream resolvers (default: system DNS or configured forwarders like 1.1.1.1)

## Windows Host Configuration

### Static Route to Isolated Network

Required to enable Windows host to reach the isolated lab network:

```powershell
route add 10.0.0.0 mask 255.255.255.0 192.168.2.100
```

This tells Windows: "To reach 10.0.0.0/24, send traffic to OPNsense WAN IP (192.168.2.100)"

**Make route persistent:**
```powershell
route add 10.0.0.0 mask 255.255.255.0 192.168.2.100 -p
```

### DNS Configuration

Changed Windows DNS to use OPNsense:
- Primary DNS: 192.168.2.100 (OPNsense WAN)
- Secondary DNS: 1.1.1.1 (optional fallback)

This enables:
- Resolution of `.homelab` domains via Unbound
- Public DNS resolution forwarded upstream
- No more `/etc/hosts` file hacks

## Kubernetes Cluster Migration

### Challenges Encountered

When moving k3s nodes from home network (192.168.2.x) to isolated network (10.0.0.x), several networking issues arose:

#### 1. Agent Nodes Couldn't Join Cluster

**Problem:** Worker nodes (homelab2, homelab3) tried to connect to old control plane IP

**Solution:** Update k3s agent configuration
```bash
# On each worker node
sudo nano /etc/systemd/system/k3s-agent.service.env

# Change K3S_URL from old IP to new:
K3S_URL=https://10.0.0.x:6443  # homelab1's new IP

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart k3s-agent
```

#### 2. Kubernetes API Endpoint Stale

**Problem:** The kubernetes service endpoint still pointed to old control plane IP

**Symptom:** 
```bash
kubectl get endpoints kubernetes -n default
# Showed: 192.168.2.37:6443 (old IP)
```

**Impact:** System pods (NFS provisioner, metrics-server) couldn't reach API server

**Solution:** Restart k3s on control plane to re-register with new IP
```bash
# On homelab1
sudo systemctl restart k3s

# Verify fix
kubectl get endpoints kubernetes -n default
# Should now show: 10.0.0.x:6443 (new IP)
```

#### 3. NFS Client Tools Missing

**Problem:** NFS provisioner pod stuck in ContainerCreating

**Error:** `mount failed: exit status 32 - you might need a /sbin/mount.<type> helper program`

**Solution:** Install NFS client utilities on all nodes
```bash
# On each k3s node
sudo apt update
sudo apt install -y nfs-common
```

### Verification Steps

After migration, verify cluster health:

```bash
# All nodes should be Ready
kubectl get nodes

# All pods should be Running
kubectl get pods -A

# Check API endpoint
kubectl get endpoints kubernetes -n default

# Test application
curl http://dashboard.homelab
```

## NFS Storage Across Networks

The QNAP NAS remains on the home network (192.168.2.133), while k3s nodes are on the isolated network (10.0.0.0/24).

**This works because:**
1. OPNsense firewall allows LAN → WAN traffic
2. Kubernetes nodes can reach 192.168.2.133 through OPNsense routing
3. NFS provisioner mounts work seamlessly across network boundaries

**NFS Configuration:**
- NFS Server: 192.168.2.133
- NFS Path: /kubernetes/persistent-volumes
- All k3s nodes have `nfs-common` installed
- Persistent volumes maintain data across pod restarts/migrations

## Benefits Achieved

### Security
- **Network Segmentation:** Lab infrastructure isolated from home network
- **Controlled Access:** Firewall rules explicitly define allowed traffic
- **Attack Surface Reduction:** Compromised lab services can't directly access home network

### Functionality
- **Service Discovery:** Clean DNS names for all services
- **Routing:** Proper network routing vs flat network
- **Production-Like:** Mirrors real-world enterprise network architecture

### Portfolio Value
- **Enterprise Skills:** Network segmentation, firewall management, DNS
- **Problem Solving:** Troubleshot complex networking issues during migration
- **Documentation:** Comprehensive documentation of the process

## Lessons Learned

### Technical Insights

1. **Hyper-V Default Switch is a Trap**
   - Default Switch has its own DHCP (172.31.x.x)
   - Creates confusion when trying to use custom networks
   - Solution: Create dedicated Internal vSwitch for isolated networks

2. **Kubernetes Doesn't Auto-Update Endpoints**
   - Changing node IPs requires manual service restarts
   - API server must re-register after IP changes
   - Agent nodes need config file updates

3. **OPNsense WAN "Block Private Networks" Setting**
   - Blocks RFC1918 addresses by default on WAN
   - Must be disabled when WAN is connected to private network
   - Found in Interface settings, NOT firewall rules

4. **Static Routes Are Essential**
   - Windows needs explicit route to reach isolated network
   - Without route, traffic goes to default gateway (ISP router)
   - Make routes persistent with `-p` flag

### Process Improvements

1. **Test with Disposable VM First**
   - Don't migrate production cluster immediately
   - Spin up test VM to verify networking
   - Saved time vs troubleshooting broken cluster

2. **Check Endpoints After IP Changes**
   - `kubectl get endpoints` shows service routing
   - Critical for diagnosing API connectivity issues
   - Should be first check when pods can't reach services

3. **System Logs Are Your Friend**
   - `kubectl describe pod` shows container events
   - `crictl logs` on nodes bypasses API
   - OPNsense firewall logs show dropped packets

## Future Enhancements

### Network
- [ ] Implement VLANs for additional network segmentation
- [ ] Add IDS/IPS using Suricata in OPNsense
- [ ] Set up VPN for remote access to lab network
- [ ] Configure high availability with second OPNsense instance

### DNS
- [ ] Implement split-horizon DNS for internal/external resolution
- [ ] Add wildcard DNS for automatic ingress routing (*.homelab)
- [ ] Set up DNSSEC validation
- [ ] Configure DNS over TLS (DoT) for upstream queries

### Monitoring
- [ ] Set up Netflow monitoring in OPNsense
- [ ] Add firewall metrics to Grafana
- [ ] Monitor network throughput between zones
- [ ] Alert on unusual traffic patterns

## Commands Reference

### OPNsense Access
```bash
# Web UI (from home network)
https://192.168.2.100

# Console access (Hyper-V)
# Connect to VM console in Hyper-V Manager
```

### Windows Networking
```powershell
# Add static route
route add 10.0.0.0 mask 255.255.255.0 192.168.2.100 -p

# Verify route
route print

# Test connectivity
ping 10.0.0.1
ping homelab1.homelab
```

### Kubernetes Troubleshooting
```bash
# Check node IPs
kubectl get nodes -o wide

# Check API endpoint
kubectl get endpoints kubernetes -n default

# Check pod networking
kubectl get pods -A -o wide

# Describe problematic pod
kubectl describe pod <pod-name> -n <namespace>

# View pod logs
kubectl logs <pod-name> -n <namespace>

# Check services
kubectl get svc -A
```

### k3s Agent Configuration
```bash
# View agent config
sudo cat /etc/systemd/system/k3s-agent.service.env

# Edit config
sudo nano /etc/systemd/system/k3s-agent.service.env

# Restart after changes
sudo systemctl daemon-reload
sudo systemctl restart k3s-agent
```

## Conclusion

Network isolation with OPNsense provides enterprise-grade network segmentation in a homelab environment. The implementation demonstrates practical skills in:

- Virtual networking and routing
- Firewall configuration and security policies
- DNS management and service discovery
- Kubernetes networking troubleshooting
- Cross-network storage integration

This foundation enables future enhancements like VPNs, IDS/IPS, and advanced monitoring while maintaining security boundaries between production and experimental workloads.

---

**Date Completed:** November 30, 2025  
**Time Investment:** ~4 hours (including troubleshooting)  
**Status:** Production - All services operational
