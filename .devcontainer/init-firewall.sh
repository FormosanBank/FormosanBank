#!/bin/bash
# Egress allowlist firewall for the FormosanBank dev container.
#
# Adapted from Anthropic's reference devcontainer firewall. Default-drops all
# outbound traffic except DNS, localhost, established connections, and a small
# allowlist (Anthropic API, GitHub, npm, PyPI, Hugging Face, VS Code). This
# closes the data-exfiltration vector so bypass-permissions mode is safe: even
# if Claude runs unattended, it can neither escape /workspace (filesystem
# isolation) nor phone arbitrary hosts (this).
#
# Runs as root (via the scoped sudoers entry) on every container start
# (postStartCommand) because iptables state does not persist across restarts.
#
# KNOWN LIMITATION: PyPI (files.pythonhosted.org) and Hugging Face serve from
# CDNs whose IPs rotate. We allowlist the IPs resolved at firewall-setup time,
# so a later pip/audio download may hit a CDN IP that isn't in the set and
# fail. The initial venv/plugin install is unaffected (postCreate runs BEFORE
# this on first create). If a later download fails, re-run this script (it
# re-resolves) or temporarily flush the firewall.
set -euo pipefail
IFS=$'\n\t'

echo "[firewall] flushing existing rules..."
iptables -F
iptables -X
iptables -t nat -F 2>/dev/null || true
iptables -t nat -X 2>/dev/null || true
iptables -t mangle -F 2>/dev/null || true
iptables -t mangle -X 2>/dev/null || true
ipset destroy allowed-domains 2>/dev/null || true

# DNS (resolution must work before we can allowlist anything by name).
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT  -p udp --sport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT  -p tcp --sport 53 -j ACCEPT

# Localhost.
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Established/related return traffic.
iptables -A INPUT  -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

ipset create allowed-domains hash:net

echo "[firewall] adding GitHub published IP ranges..."
gh_ranges=$(curl -fsSL --max-time 20 https://api.github.com/meta || true)
if echo "$gh_ranges" | jq -e '.web and .api and .git' >/dev/null 2>&1; then
    echo "$gh_ranges" | jq -r '(.web + .api + .git)[]' | aggregate -q 2>/dev/null | while read -r cidr; do
        [[ -n "$cidr" ]] && ipset add allowed-domains "$cidr" 2>/dev/null || true
    done
else
    echo "[firewall] WARNING: could not fetch GitHub meta; git/plugin fetches may be limited."
fi

echo "[firewall] resolving allowlisted domains..."
for domain in \
    api.anthropic.com \
    console.anthropic.com \
    claude.ai \
    statsig.anthropic.com \
    statsig.com \
    sentry.io \
    registry.npmjs.org \
    pypi.org \
    files.pythonhosted.org \
    huggingface.co \
    cdn-lfs.huggingface.co \
    cdn-lfs-us-1.huggingface.co \
    marketplace.visualstudio.com \
    update.code.visualstudio.com ; do
    ips=$(dig +short A "$domain" 2>/dev/null || true)
    for ip in $ips; do
        if [[ "$ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
            ipset add allowed-domains "$ip" 2>/dev/null || true
        fi
    done
done

# Allow outbound to the allowlist; drop everything else.
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT
iptables -P INPUT   DROP
iptables -P FORWARD DROP
iptables -P OUTPUT  DROP

# --- Self-test ---------------------------------------------------------------
# Never silently break Claude and never silently leave the user unprotected.
echo "[firewall] self-test..."

# 1) An arbitrary host must be BLOCKED. If it isn't, the firewall isn't doing
#    its job (e.g. NET_ADMIN missing) — warn LOUDLY but don't make things worse.
if curl -fsSL --max-time 5 https://example.com >/dev/null 2>&1; then
    echo "[firewall] ############################################################" >&2
    echo "[firewall] WARNING: example.com is REACHABLE — egress is NOT blocked." >&2
    echo "[firewall] The firewall is INEFFECTIVE. Do NOT rely on bypass mode" >&2
    echo "[firewall] being safe; investigate (NET_ADMIN capability? ipset?)." >&2
    echo "[firewall] ############################################################" >&2
fi

# 2) The Anthropic API must be REACHABLE (401/403 still means we connected). If
#    it's blocked, Claude can't work — flush the firewall to restore it rather
#    than leaving a broken lockdown, and warn that protection is OFF.
if ! curl -sS --max-time 10 -o /dev/null https://api.anthropic.com/v1/models 2>/dev/null; then
    echo "[firewall] ############################################################" >&2
    echo "[firewall] ERROR: api.anthropic.com is unreachable through the firewall." >&2
    echo "[firewall] Flushing rules to restore Claude. FIREWALL IS OFF — fix the" >&2
    echo "[firewall] allowlist before relying on bypass-permissions mode." >&2
    echo "[firewall] ############################################################" >&2
    iptables -P INPUT ACCEPT; iptables -P OUTPUT ACCEPT; iptables -P FORWARD ACCEPT
    iptables -F
    exit 1
fi

echo "[firewall] OK: arbitrary egress blocked; Anthropic API reachable."
