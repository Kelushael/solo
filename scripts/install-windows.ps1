$HostIP = "108.181.162.206"
$User = "administrator"
$KeyPath = "$env:USERPROFILE\.ssh\solo_agent_ed25519"

if (!(Test-Path "$env:USERPROFILE\.ssh")) {
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh" | Out-Null
}

if (!(Test-Path $KeyPath)) {
    ssh-keygen -t ed25519 -f $KeyPath -N ""
}

$PubKey = Get-Content "$KeyPath.pub" -Raw

ssh "$User@$HostIP" "mkdir -p ~/.ssh && echo '$PubKey' >> ~/.ssh/authorized_keys"

Add-Content $PROFILE "function solo { ssh -i '$KeyPath' $User@$HostIP }"

Write-Host "✅ Installed. Use: solo"
