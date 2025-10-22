// monitor.c
#include <windows.h>
#include <pdh.h>
#include <stdio.h>

#pragma comment(lib, "pdh.lib")

double get_cpu_usage() {
    static PDH_HQUERY cpuQuery;
    static PDH_HCOUNTER cpuTotal;
    static int initialized = 0;
    PDH_FMT_COUNTERVALUE counterVal;

    if (!initialized) {
        PdhOpenQuery(NULL, NULL, &cpuQuery);
        PdhAddCounter(cpuQuery, "\\Processor(_Total)\\% Processor Time", NULL, &cpuTotal);
        PdhCollectQueryData(cpuQuery);
        initialized = 1;
        Sleep(1000);
    }

    PdhCollectQueryData(cpuQuery);
    PdhGetFormattedCounterValue(cpuTotal, PDH_FMT_DOUBLE, NULL, &counterVal);

    return counterVal.doubleValue;
}

void get_memory_usage(DWORDLONG *totalPhysMem, DWORDLONG *physMemUsedPercent) {
    MEMORYSTATUSEX memStatus;
    memStatus.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&memStatus)) {
        *totalPhysMem = memStatus.ullTotalPhys / (1024 * 1024); // em MB
        *physMemUsedPercent = memStatus.dwMemoryLoad; // em %
    } else {
        *totalPhysMem = 0;
        *physMemUsedPercent = 0;
    }
}

int main() {
    double cpuUsage;
    DWORDLONG totalMemMB;
    DWORDLONG memUsedPercent;

    cpuUsage = get_cpu_usage();
    get_memory_usage(&totalMemMB, &memUsedPercent);

    printf("CPU Usage: %.2f%%\n", cpuUsage);
    printf("Memory Usage: %llu MB used (%.2llu%%)\n", totalMemMB, memUsedPercent);

    return 0;
}
