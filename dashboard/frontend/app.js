// Self-Healing Cloud Dashboard JavaScript Client

let trafficChart = null;
const maxDataPoints = 15;
const chartLabels = [];
const rpsData = [];
const latencyData = [];

document.addEventListener("DOMContentLoaded", () => {
    initChart();
    refreshData();
    setInterval(refreshData, 3000); // Poll every 3 seconds
});

function initChart() {
    const ctx = document.getElementById("trafficChart").getContext("2d");
    for (let i = 0; i < maxDataPoints; i++) {
        chartLabels.push("");
        rpsData.push(0);
        latencyData.push(0);
    }

    trafficChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartLabels,
            datasets: [
                {
                    label: "Throughput (RPS)",
                    data: rpsData,
                    borderColor: "#06b6d4", // Cyan
                    backgroundColor: "rgba(6, 182, 212, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: "y"
                },
                {
                    label: "P95 Latency (ms)",
                    data: latencyData,
                    borderColor: "#f59e0b", // Amber
                    backgroundColor: "transparent",
                    borderWidth: 2,
                    borderDash: [4, 4],
                    tension: 0.3,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    grid: { color: "#1e293b" },
                    ticks: { color: "#94a3b8", font: { size: 10 } },
                    suggestedMin: 0,
                    suggestedMax: 10
                },
                y1: {
                    type: "linear",
                    display: true,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    ticks: { color: "#94a3b8", font: { size: 10 } },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: {
                    labels: { color: "#cbd5e1", font: { size: 11 }, boxWidth: 12 }
                }
            }
        }
    });
}

async function refreshData() {
    const refreshIcon = document.getElementById("refresh-icon");
    if (refreshIcon) refreshIcon.classList.add("fa-spin");

    try {
        await Promise.all([
            fetchClusterState(),
            fetchMetricsSummary(),
            fetchSystemInfo(),
            fetchExperiments()
        ]);
    } catch (e) {
        console.error("Dashboard refresh error:", e);
    } finally {
        if (refreshIcon) refreshIcon.classList.remove("fa-spin");
    }
}

async function fetchClusterState() {
    const res = await fetch("/api/system/cluster");
    if (!res.ok) return;
    const data = await res.json();

    // Render Pod Fleet
    const podGrid = document.getElementById("pod-grid");
    const countBadge = document.getElementById("pod-fleet-count");
    const pods = data.pods || [];

    countBadge.innerText = `${pods.length} Pods`;
    let healthyCount = 0;

    if (pods.length === 0) {
        podGrid.innerHTML = `
            <div class="p-4 rounded-lg bg-slate-800/40 border border-slate-800 text-xs text-slate-400 col-span-2 text-center">
                No active pods in namespace. Deploying or starting up.
            </div>`;
    } else {
        let html = "";
        pods.forEach(pod => {
            if (pod.ready) healthyCount++;
            const statusColor = pod.ready ? "emerald" : "rose";
            const statusIcon = pod.ready ? "fa-circle-check" : "fa-triangle-exclamation";
            
            html += `
            <div class="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 hover:border-slate-600 transition flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex items-center space-x-2">
                            <span class="h-2.5 w-2.5 rounded-full bg-${statusColor}-400 ${pod.ready ? 'pulse-healthy' : ''}"></span>
                            <span class="font-mono font-semibold text-xs text-slate-200 truncate max-w-[170px]" title="${pod.name}">
                                ${pod.name}
                            </span>
                        </div>
                        <span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-${statusColor}-500/10 text-${statusColor}-400 border border-${statusColor}-500/20">
                            ${pod.phase}
                        </span>
                    </div>

                    <div class="space-y-1 text-[11px] text-slate-400">
                        <div class="flex justify-between">
                            <span>Pod IP:</span>
                            <span class="font-mono text-slate-300">${pod.pod_ip || 'N/A'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Restarts:</span>
                            <span class="font-mono ${pod.restart_count > 0 ? 'text-amber-400 font-semibold' : 'text-slate-300'}">
                                ${pod.restart_count}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span>Age:</span>
                            <span class="text-slate-300">${pod.age_seconds}s</span>
                        </div>
                    </div>
                </div>

                <div class="mt-3 pt-2.5 border-t border-slate-700/50 flex gap-2">
                    <button onclick="killSpecificPod('${pod.name}')" class="w-full py-1 px-2 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-[10px] font-medium transition flex items-center justify-center gap-1">
                        <i class="fa-solid fa-skull"></i> Terminate Pod
                    </button>
                </div>
            </div>`;
        });
        podGrid.innerHTML = html;
    }

    // Update Top KPIs
    document.getElementById("stat-healthy-pods").innerText = healthyCount;
    const desired = data.deployment ? data.deployment.desired_replicas : pods.length;
    document.getElementById("stat-total-pods").innerText = `/ ${desired} desired`;
    
    // Update HPA card
    if (data.hpa) {
        const hpa = data.hpa;
        document.getElementById("stat-hpa-replicas").innerText = `${hpa.current_replicas} / ${hpa.max_replicas}`;
        document.getElementById("stat-hpa-limits").innerText = `Min ${hpa.min_replicas} / Max ${hpa.max_replicas}`;
        document.getElementById("stat-hpa-cpu").innerText = `Target: ${hpa.target_cpu_utilization || 60}% CPU`;
        
        document.getElementById("hpa-curr-rep").innerText = hpa.current_replicas;
        document.getElementById("hpa-des-rep").innerText = hpa.desired_replicas;
        document.getElementById("hpa-bounds").innerText = `Min ${hpa.min_replicas} • Max ${hpa.max_replicas}`;
        
        const currCpu = hpa.current_cpu_utilization !== null ? hpa.current_cpu_utilization : 0;
        const targetCpu = hpa.target_cpu_utilization || 60;
        document.getElementById("hpa-cpu-text").innerText = `${currCpu}% / ${targetCpu}%`;
        const pctWidth = Math.min(100, Math.round((currCpu / 100) * 100));
        document.getElementById("hpa-cpu-bar").style.width = `${pctWidth}%`;
        if (currCpu > targetCpu) {
            document.getElementById("hpa-cpu-bar").className = "bg-rose-500 h-2.5 rounded-full transition-all duration-500";
        } else {
            document.getElementById("hpa-cpu-bar").className = "bg-indigo-500 h-2.5 rounded-full transition-all duration-500";
        }
    }
}

async function fetchMetricsSummary() {
    const res = await fetch("/api/system/metrics");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("stat-rps").innerText = data.rps !== undefined ? data.rps : "0.0";
    document.getElementById("stat-latency").innerText = data.p95_latency_ms !== undefined ? data.p95_latency_ms : "0.0";
    document.getElementById("stat-error-rate").innerText = data.error_rate !== undefined ? data.error_rate : "0.0";

    // Update Live Chart
    if (trafficChart) {
        rpsData.shift();
        rpsData.push(data.rps || 0);
        latencyData.shift();
        latencyData.push(data.p95_latency_ms || 0);
        trafficChart.update();
    }
}

async function fetchSystemInfo() {
    const res = await fetch("/api/system/info");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("footer-node").innerText = data.node_name || "minikube";
    document.getElementById("footer-pod").innerText = data.pod_name || "standalone";
    document.getElementById("footer-mem").innerText = `${data.memory_used_mb} MB (${data.memory_percent}%)`;
    document.getElementById("footer-k8s").innerText = data.k8s_connected ? "Connected" : "Standalone";
    document.getElementById("footer-k8s").className = data.k8s_connected ? "text-emerald-400" : "text-amber-400";
}

async function fetchExperiments() {
    const res = await fetch("/api/experiments");
    if (!res.ok) return;
    const list = await res.json();

    const tbody = document.getElementById("experiments-table-body");
    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-500 font-sans">No experiments recorded yet. Click "Run MTTR Benchmark" above.</td></tr>`;
        return;
    }

    let html = "";
    list.slice(0, 10).forEach(exp => {
        const statusColor = exp.status === "RECOVERED" || exp.status === "COMPLETED" ? "emerald" : "amber";
        html += `
        <tr class="hover:bg-slate-800/30 transition">
            <td class="py-2.5 px-3 font-semibold text-slate-200">${exp.experiment_id}</td>
            <td class="py-2.5 px-3 font-sans text-slate-300">${exp.scenario}</td>
            <td class="py-2.5 px-3 text-slate-400">${exp.initial_replicas} &rarr; ${exp.final_replicas}</td>
            <td class="py-2.5 px-3 text-cyan-300">${exp.recovery_time_seconds ? exp.recovery_time_seconds + 's' : 'N/A'}</td>
            <td class="py-2.5 px-3">
                <span class="px-2 py-0.5 rounded text-[10px] bg-${statusColor}-500/10 text-${statusColor}-400 border border-${statusColor}-500/20">
                    ${exp.status}
                </span>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

// Chaos Injections
async function triggerFault(faultType, duration = 30) {
    try {
        const res = await fetch("/api/chaos/trigger", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fault_type: faultType, duration_seconds: duration })
        });
        const data = await res.json();
        
        const banner = document.getElementById("chaos-banner");
        const bannerText = document.getElementById("chaos-banner-text");
        bannerText.innerText = data.message;
        banner.classList.remove("hidden");
        
        setTimeout(refreshData, 1000);
    } catch (e) {
        alert("Failed to inject fault: " + e);
    }
}

async function killSpecificPod(podName) {
    if (!confirm(`Are you sure you want to terminate pod ${podName}? Kubernetes controller will detect and recover it.`)) return;
    try {
        const res = await fetch(`/api/chaos/trigger`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fault_type: "delete-pod" })
        });
        refreshData();
    } catch (e) {
        alert("Error deleting pod: " + e);
    }
}

async function resetChaos() {
    try {
        await fetch("/api/chaos/reset", { method: "POST" });
        const banner = document.getElementById("chaos-banner");
        banner.classList.add("hidden");
        refreshData();
    } catch (e) {
        alert("Failed to reset: " + e);
    }
}

async function triggerWorkload(type, seconds, intensity = 80) {
    try {
        fetch(`/workload/${type}?seconds=${seconds}&intensity=${intensity}`);
        alert(`Dispatched synthetic ${type.toUpperCase()} workload for ${seconds} seconds.`);
        setTimeout(refreshData, 1500);
    } catch (e) {
        console.error(e);
    }
}

async function runMttrBenchmark() {
    try {
        const res = await fetch("/api/experiments/run-self-healing-test", { method: "POST" });
        const data = await res.json();
        alert("MTTR Benchmark initiated! Kubernetes will replace the pod and log recovery duration to the experiment history table.");
        setTimeout(refreshData, 3000);
        setTimeout(refreshData, 10000);
        setTimeout(refreshData, 20000);
    } catch (e) {
        alert("Error starting benchmark: " + e);
    }
}
