param(
    [string]$PostUrl = "https://coomer.st/fansly/user/486232478122516480/post/783095922266480640",
    [string]$ApiUrl = "https://coomer.st/api/v1/fansly/user/486232478122516480/posts"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Url {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $agents = @{
        Chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        Firefox = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        Safari = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
    }

    Write-Host ""
    Write-Host "=== $Label ==="
    Write-Host "URL: $Url"
    foreach ($name in $agents.Keys) {
        $handler = $null
        $client = $null
        try {
            $handler = [System.Net.Http.HttpClientHandler]::new()
            $client = [System.Net.Http.HttpClient]::new($handler)
            $client.Timeout = [TimeSpan]::FromSeconds(20)
            $client.DefaultRequestHeaders.UserAgent.ParseAdd($agents[$name])

            $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Head, $Url)
            $response = $client.SendAsync($request).GetAwaiter().GetResult()
            $statusCode = [int]$response.StatusCode
            $length = if ($response.Content.Headers.ContentLength) { [string]$response.Content.Headers.ContentLength } else { "n/a" }
            Write-Host ("[{0}] status={1} content-length={2}" -f $name, $statusCode, $length)
        } catch {
            Write-Host ("[{0}] status=ERR message={1}" -f $name, $_.Exception.Message)
        } finally {
            if ($client) { $client.Dispose() }
            if ($handler) { $handler.Dispose() }
        }
    }
}

Write-Host "Coomer playback diagnostics"
Write-Host "Started: $(Get-Date -Format s)"

Write-Host ""
Write-Host "=== DNS Baseline (coomer.st) ==="
foreach ($dns in @("default", "1.1.1.1", "8.8.8.8")) {
    try {
        if ($dns -eq "default") {
            $ips = Resolve-DnsName coomer.st -Type A | Select-Object -ExpandProperty IPAddress
        } else {
            $ips = Resolve-DnsName coomer.st -Type A -Server $dns | Select-Object -ExpandProperty IPAddress
        }
        Write-Host ("[{0}] {1}" -f $dns, ($ips -join ", "))
    } catch {
        Write-Host ("[{0}] DNS lookup failed: {1}" -f $dns, $_.Exception.Message)
    }
}

try {
    ipconfig /flushdns | Out-Null
    Write-Host "DNS cache flushed."
} catch {
    Write-Host "DNS cache flush failed (non-fatal)."
}

Test-Url -Url $PostUrl -Label "Post page reachability"
Test-Url -Url $ApiUrl -Label "API reachability"

Write-Host ""
Write-Host "=== Interpretation ==="
Write-Host "- Post=200 but API=403 usually means server-side filtering/rate-limit/fingerprint."
Write-Host "- DNS resolves but browser still fails => likely browser profile/extension/network path issue."
Write-Host "- If both post and API fail with connection errors => route/ISP/VPN problem."

Write-Host ""
Write-Host "=== Recommended fallback profile ==="
Write-Host "1) Firefox private window, no extensions for this site."
Write-Host "2) DNS 1.1.1.1 or 8.8.8.8."
Write-Host "3) If playback still fails, switch to mobile data or trusted VPN exit."
Write-Host "4) Retry once after 20-40s wait on page load."
