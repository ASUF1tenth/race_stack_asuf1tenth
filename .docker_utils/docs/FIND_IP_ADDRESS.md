## Step 1: Get your local IP

```bash
hostname -I
```

If this returns 192.168.1.15, your network range is 192.168.1.0/24.

## Step 2: Fast scan the network without DNS resolution

```bash
nmap -n 192.168.1.0/24
```

(Using sudo here is highly recommended because it allows Nmap to use raw ARP packets, making the scan incredibly fast and accurate on local networks).

## Step 3: View the discovered devices

```bash
arp -a
```

(Tip: look for the connected devices on your hotspot to know the mac address of the remote device)
