<template>
   <navbar />
    <div class="p-4 sm:p-8">
        <div class="container mx-auto p-6 card">
            <h1 class="hh1 text-center">室內煤倉廢水處理廠回收水每日用量</h1>
            <div class="card p-4 mb-4 flex items-center justify-between">
                <h2 class="text-lg font-semibold text-gray-800">T3000 OPC 連線狀態:</h2>
                <div id="opcStatus" class="font-bold" :style="{ color: opcStatusColor }">{{ opcStatus }}</div>
            </div>

            <div class="grid md:grid-cols-2 gap-8 mb-8">
                <div class="card p-6 flex flex-col items-center text-center">
                    <h2 class="text-xl font-semibold mb-2 text-gray-800">最新回收水累計量</h2>
                    <div id="latestValueContainer" class="flex items-center gap-2 mb-2">
                        <span id="latestValue" class="text-4xl font-extrabold text-blue-600">{{ latestValue }}</span>
                        <span class="text-lg text-gray-500">m³</span>
                    </div>
                    <p class="text-sm text-gray-500">
                        Last updated at: <span id="latestTimestamp" class="font-medium text-gray-600">{{ latestTimestamp }}</span>
                    </p>
                </div>

                <div class="card p-6 flex flex-col items-center text-center">
                    <h2 class="text-xl font-semibold mb-2 text-gray-800">前一日回收水最後累計量</h2>
                    <div id="previousDayValueContainer" class="flex items-center gap-2 mb-2">
                        <span id="previousDayValue" class="text-4xl font-extrabold text-slate-600">{{ previousDayValue }}</span>
                        <span class="text-lg text-gray-500">m³</span>
                    </div>
                    <p class="text-sm text-gray-500">
                        Last updated at: <span id="previousDayTimestamp" class="font-medium text-gray-600">{{ previousDayTimestamp }}</span>
                    </p>
                </div>
            </div>

            <div class="flex flex-col md:flex-row items-center justify-center gap-4 mb-8">
                <div class="w-full md:w-1/3">
                    <label for="startDate" class="block text-sm font-medium text-gray-700 mb-1">Start Date:</label>
                    <input type="date" id="startDate" class="flatpickr-input" v-model="startDate">
                </div>
                <div class="w-full md:w-1/3">
                    <label for="endDate" class="block text-sm font-medium text-gray-700 mb-1">End Date:</label>
                    <input type="date" id="endDate" class="flatpickr-input" v-model="endDate">
                </div>
                <div class="w-full md:w-auto mt-4 md:mt-0 flex gap-4">
                    <button id="fetchDataBtn" class="btn-primary w-full md:w-auto" @click="fetchData" :disabled="isLoading">
                        <span v-if="isLoading">Loading...</span>
                        <span v-else>顯示每日回收水用量</span>
                    </button>
                    <button id="exportExcelBtn" class="btn-secondary w-full md:w-auto" @click="exportExcel" :disabled="!currentTableData.length || isLoading">匯出至Excel檔</button>
                </div>
            </div>

            <div id="loadingIndicator" class="text-center text-blue-600 font-semibold mb-4" :class="{ 'hidden': !isLoading }">
                Loading data...
            </div>

            <div id="resultsContainer" class="overflow-x-auto">
                <table class="min-w-full bg-white rounded-lg overflow-hidden">
                    <thead>
                        <tr class="table-header">
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">日期</th>
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">用量(m³)</th>
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">當日最終累計量(m³)</th>
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">當日最終時間戳</th>
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">前一日最終累計量(m³)</th>
                            <th class="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider">前一日最終時間戳</th>
                        </tr>
                    </thead>
                    <tbody id="waterUsageTableBody">
                        <tr v-if="currentTableData.length === 0 && !isLoading">
                            <td colspan="6" class="py-4 px-4 text-center text-gray-500">
                                選擇日期區間再點選"顯示每日回收水用量". 2025/8/7程式啟用, 2025/8/7後才會有每日用量
                            </td>
                        </tr>
                        <tr v-else-if="currentTableData.length === 0 && !isLoading && fetchError">
                            <td colspan="6" class="py-4 px-4 text-center text-red-500">
                                {{ fetchError }}
                            </td>
                        </tr>
                        <template v-else>
                            <tr v-for="item in currentTableData" :key="item.date" class="table-row">
                                <td class="py-3 px-4 whitespace-nowrap">{{ item.date }}</td>
                                <td class="py-3 px-4 whitespace-nowrap">{{ formatUsage(item.daily_usage) }}</td>
                                <td class="py-3 px-4 whitespace-nowrap">{{ formatUsage(item.today_last_usage) }}</td>
                                <td class="py-3 px-4 whitespace-nowrap">{{ formatTimestamp(item.today_last_usage_timestamp) }}</td>
                                <td class="py-3 px-4 whitespace-nowrap">{{ formatUsage(item.previous_day_last_usage) }}</td>
                                <td class="py-3 px-4 whitespace-nowrap">{{ formatTimestamp(item.previous_day_last_usage_timestamp) }}</td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <div id="messageBox" class="message-box" :class="{ 'show': messageShow }" :style="{ backgroundColor: messageTypeColor }">{{ messageText }}</div>
    </div>
    <footbar />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';

// Get runtime config
const config = useRuntimeConfig();
const apiBase = config.public.apiBase;

// --- Reactive State ---
const opcStatus = ref('Connecting...');
const latestValue = ref('--');
const latestTimestamp = ref('--');
const previousDayValue = ref('--');
const previousDayTimestamp = ref('--');
const startDate = ref(new Date().toISOString().slice(0, 10));
const endDate = ref(new Date().toISOString().slice(0, 10));
const currentTableData = ref([]);
const isLoading = ref(false);
const fetchError = ref('');

// Message Box State
const messageText = ref('');
const messageShow = ref(false);
const messageType = ref('success'); // 'success' or 'error'

// --- Computed Properties ---
const opcStatusColor = computed(() => {
    if (opcStatus.value === 'Normal') return '#10B981';
    if (opcStatus.value === 'No Connection') return '#EF4444';
    return '#F59E0B'; // Default/Connecting
});

const messageTypeColor = computed(() => {
    return messageType.value === 'error' ? '#f44336' : '#4CAF50';
});

// --- Utility Functions ---
function showMessage(message, type = 'success') {
    messageText.value = message;
    messageType.value = type;
    messageShow.value = true;
    setTimeout(() => {
        messageShow.value = false;
    }, 3000);
}

function formatUsage(value) {
    return value !== null ? `${value.toFixed(3)} m³` : '--';
}

function formatTimestamp(timestamp) {
    return timestamp ? new Date(timestamp).toLocaleString() : '--';
}

// --- API Fetch Methods ---

async function fetchOpcStatus() {
    try {
        const response = await fetch(`${apiBase}/api/opc_status`);
        const data = await response.json();
        opcStatus.value = data.status;
    } catch (error) {
        console.error('Error fetching OPC status:', error);
        opcStatus.value = 'Error';
    }
}

async function fetchLatestData() {
    try {
        const response = await fetch(`${apiBase}/api/latest_water_usage`);
        const data = await response.json();

        if (response.ok && data.latest_accumulated_value !== null) {
            latestValue.value = data.latest_accumulated_value.toFixed(3);
            latestTimestamp.value = data.latest_timestamp ? new Date(data.latest_timestamp).toLocaleString() : 'No data available';
        } else {
            latestValue.value = '--';
            latestTimestamp.value = 'No data available';
        }

        if (data.previous_day_accumulated_value !== null) {
            previousDayValue.value = data.previous_day_accumulated_value.toFixed(3);
            previousDayTimestamp.value = data.previous_day_timestamp ? new Date(data.previous_day_timestamp).toLocaleString() : 'Timestamp not available';
        } else {
            previousDayValue.value = '--';
            previousDayTimestamp.value = 'No data available';
        }

    } catch (error) {
        console.error('Error fetching latest water usage data:', error);
        latestValue.value = '--';
        latestTimestamp.value = 'Error loading data';
        previousDayValue.value = '--';
        previousDayTimestamp.value = 'Error loading data';
    }
}

async function fetchData() {
    if (!startDate.value || !endDate.value) {
        showMessage('Please select both start and end dates.', 'error');
        return;
    }

    if (new Date(startDate.value) > new Date(endDate.value)) {
        showMessage('Start date cannot be after end date.', 'error');
        return;
    }

    isLoading.value = true;
    currentTableData.value = [];
    fetchError.value = '';

    try {
        const response = await fetch(`${apiBase}/api/water_usage?start_date_str=${startDate.value}&end_date_str=${endDate.value}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to fetch data');
        }

        currentTableData.value = data;

        if (data.length === 0) {
            fetchError.value = 'No water usage data found for the selected period.';
        }

        showMessage('Water usage data loaded successfully!');

    } catch (error) {
        console.error('Error fetching water usage data:', error);
        fetchError.value = `Error loading data: ${error.message}. Please try again.`;
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        isLoading.value = false;
    }
}

function exportExcel() {
    if (currentTableData.value.length === 0) {
        showMessage('No data to export. Please fetch data first.', 'error');
        return;
    }

    // Assuming XLSX is available globally
    if (typeof window.XLSX === 'undefined') {
        showMessage('XLSX library not loaded. Cannot export.', 'error');
        return;
    }

    const dataToExport = currentTableData.value.map(item => ({
        '日期': item.date,
        '用量(m³)': item.daily_usage !== null ? item.daily_usage.toFixed(3) : '--',
        '當日最終累計量(m³)': item.today_last_usage !== null ? item.today_last_usage.toFixed(3) : '--',
        '當日最終時間戳': formatTimestamp(item.today_last_usage_timestamp),
        '前一日最終累計量(m³)': item.previous_day_last_usage !== null ? item.previous_day_last_usage.toFixed(3) : '--',
        '前一日最終時間戳': formatTimestamp(item.previous_day_last_usage_timestamp)
    }));

    const worksheet = window.XLSX.utils.json_to_sheet(dataToExport);
    const workbook = window.XLSX.utils.book_new();
    window.XLSX.utils.book_append_sheet(workbook, worksheet, 'Water Usage Data');

    const fileName = 'water_usage_data.xlsx';
    window.XLSX.writeFile(workbook, fileName);

    showMessage(`Data exported to ${fileName}!`);
}

// --- Lifecycle Hooks ---
onMounted(() => {
    // Initialize Flatpickr (assuming it's loaded globally)
    if (typeof window.flatpickr !== 'undefined') {
        window.flatpickr('#startDate', {
            dateFormat: 'Y-m-d',
            defaultDate: startDate.value
        });
        window.flatpickr('#endDate', {
            dateFormat: 'Y-m-d',
            defaultDate: endDate.value
        });
    }

    fetchLatestData();
    fetchOpcStatus();
    // Set intervals
    const latestDataInterval = setInterval(fetchLatestData, 30000);
    const opcStatusInterval = setInterval(fetchOpcStatus, 30000);

    // Clear intervals when component is unmounted (good practice)
    // onUnmounted(() => {
    //     clearInterval(latestDataInterval);
    //     clearInterval(opcStatusInterval);
    // });
});
</script>

<style scoped>
/* Copied and adapted from the original HTML's style block */
body {
    font-family: sans-serif;
    background-color: #f0f4f8;
    color: #334155;
}
.container {
    max-width: 900px;
}
.card {
    background-color: #ffffff;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border-radius: 0.75rem; /* rounded-xl */
}
.btn-primary {
    background-color: #3b82f6;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s ease-in-out;
}
.btn-primary:hover {
    background-color: #2563eb;
}
.btn-primary:disabled {
    background-color: #93c5fd; /* light blue for disabled */
    cursor: not-allowed;
}
.btn-secondary {
    background-color: #64748b;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s ease-in-out;
}
.btn-secondary:hover {
    background-color: #475569;
}
.btn-secondary:disabled {
    background-color: #94a3b8; /* light gray/slate for disabled */
    cursor: not-allowed;
}
.table-header {
    background-color: #e2e8f0;
    color: #475569;
}
.table-row:nth-child(even) {
    background-color: #f8fafc;
}
.table-row:hover {
    background-color: #e0f2fe;
}
.flatpickr-input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #cbd5e1;
    border-radius: 0.5rem;
    font-size: 1rem;
    color: #475569;
    transition: border-color 0.2s ease-in-out;
}
.flatpickr-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}
.message-box {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background-color: #4CAF50;
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.5s ease-in-out;
    pointer-events: none;
}
.message-box.show {
    opacity: 1;
    pointer-events: auto;
}
 .hh1 {
    color: #1a202c; /* Darker text for heading */
    margin-bottom: 24px;
    font-size: 3rem; /* Doubled heading size */
    font-weight: 800; /* Extra bold */
}
</style>