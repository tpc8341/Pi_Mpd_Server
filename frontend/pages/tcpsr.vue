<template>
   <navbar />
  <div class="main-container mx-auto p-6 card">
    <div class="hh1">室內煤倉佈煤機/刮取煤機位置</div>

    <div class="status-container">
      <h2 class="status-label">T3000 OPC 連線狀態:</h2>
      <div
        id="opcStatus"
        :class="['status-text', opcStatusClass]"
      >
        {{ opcStatusText }}
      </div>
    </div>

    <div class="group-container group-tc">
      <div class="line-container" id="line1">
        <div
          class="machine-marker tc-marker"
          :style="{ left: getMarkerPosition(positions.tc75a.value) }"
        >
          TC-75A
        </div>
        <div
          class="machine-marker psr-marker"
          :style="{ left: getMarkerPosition(positions.psra1.value) }"
        >
          PSR-A1
        </div>
      </div>
      <div class="machines-grid">
        <MachineCard
          name="TC-75A"
          icon="🔩"
          :position="positions.tc75a.value"
          :timestamp="positions.tc75a.timestamp"
        />
        <MachineCard
          name="PSR-A1"
          icon="🔗"
          :position="positions.psra1.value"
          :timestamp="positions.psra1.timestamp"
        />
      </div>
    </div>

    <div class="group-container group-psra">
      <div class="line-container" id="line2">
        <div
          class="machine-marker tc-marker"
          :style="{ left: getMarkerPosition(positions.tc75b.value) }"
        >
          TC-75B
        </div>
        <div
          class="machine-marker psr-marker"
          :style="{ left: getMarkerPosition(positions.psrb1.value) }"
        >
          PSR-B1
        </div>
      </div>
      <div class="machines-grid">
        <MachineCard
          name="TC-75B"
          icon="🔩"
          :position="positions.tc75b.value"
          :timestamp="positions.tc75b.timestamp"
        />
        <MachineCard
          name="PSR-B1"
          icon="🔗"
          :position="positions.psrb1.value"
          :timestamp="positions.psrb1.timestamp"
        />
      </div>
    </div>

    <div class="group-container group-tc2">
      <div class="line-container" id="line3">
        <div
          class="machine-marker tc-marker"
          :style="{ left: getMarkerPosition(positions.tc75c.value) }"
        >
          TC-75C
        </div>
        <div
          class="machine-marker psr-marker"
          :style="{ left: getMarkerPosition(positions.psrc1.value) }"
        >
          PSR-C1
        </div>
      </div>
      <div class="machines-grid">
        <MachineCard
          name="TC-75C"
          icon="🔩"
          :position="positions.tc75c.value"
          :timestamp="positions.tc75c.timestamp"
        />
        <MachineCard
          name="PSR-C1"
          icon="🔗"
          :position="positions.psrc1.value"
          :timestamp="positions.psrc1.timestamp"
        />
      </div>
    </div>

    <div class="group-container group-psrb">
      <div class="line-container" id="line4">
        <div
          class="machine-marker tc-marker"
          :style="{ left: getMarkerPosition(positions.tc75d.value) }"
        >
          TC-75D
        </div>
        <div
          class="machine-marker psr-marker"
          :style="{ left: getMarkerPosition(positions.psrd1.value) }"
        >
          PSR-D1
        </div>
      </div>
      <div class="machines-grid">
        <MachineCard
          name="TC-75D"
          icon="🔩"
          :position="positions.tc75d.value"
          :timestamp="positions.tc75d.timestamp"
        />
        <MachineCard
          name="PSR-D1"
          icon="🔗"
          :position="positions.psrd1.value"
          :timestamp="positions.psrd1.timestamp"
        />
      </div>
    </div>
  </div>
  <footbar />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

// Define the MachineCard as a local component for reusability
const MachineCard = {
  props: {
    name: String,
    icon: String,
    position: Number,
    timestamp: Number,
  },
  setup(props) {
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return '';
      const date = new Date(timestamp * 1000); // Convert seconds to milliseconds
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      const seconds = date.getSeconds().toString().padStart(2, '0');

      return `Last updated at: ${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
    };

    const formattedTime = computed(() => formatTimestamp(props.timestamp));

    return {
      formattedTime,
    };
  },
  template: `
    <div class="machine-card">
      <div class="machine-icon">{{ icon }}</div>
      <div class="machine-name">{{ name }}</div>
      <div class="position-label">Current Position:</div>
      <div class="position-value">{{ position.toFixed(2) }}</div>
      <div class="timestamp-label">{{ formattedTime }}</div>
    </div>
  `,
};

// --- Reactive State ---
const LINE_LENGTH = 600;
const opcStatusText = ref('Connecting...');
let socket = null;

// Initial state for machine positions
const initialPosition = { value: 0.00, timestamp: null };
const positions = ref({
  tc75a: { ...initialPosition },
  psra1: { ...initialPosition },
  tc75b: { ...initialPosition },
  psrb1: { ...initialPosition },
  tc75c: { ...initialPosition },
  psrc1: { ...initialPosition },
  tc75d: { ...initialPosition },
  psrd1: { ...initialPosition },
});

// --- Computed Properties ---
const opcStatusClass = computed(() => {
  const status = opcStatusText.value;
  if (status === 'Connected') return 'status-connected';
  if (status.includes('Connecting') || status.includes('Reconnecting'))
    return 'status-connecting';
  return 'status-disconnected'; // Includes 'Disconnected' and 'Error'
});

// --- Methods ---
const getMarkerPosition = (position) => {
  const percentage = (position / LINE_LENGTH) * 100;
  // Clamp the percentage between 0 and 100
  return `${Math.max(0, Math.min(100, percentage))}%`;
};

const updateOpcStatus = (status) => {
  if (status) {
    opcStatusText.value = status;
  }
};

const connectWebSocket = () => {
  // Determine the WebSocket URL based on the current host
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connection opened');
    // Status update is typically received as a message, but set connecting initially
    updateOpcStatus('Connecting...'); 
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('Received data:', data);

      // Update OPC Status
      if (data.opc_status !== undefined) {
        updateOpcStatus(data.opc_status);
      }

      // Update machine positions
      if (data.positions) {
        for (const key in data.positions) {
          if (positions.value[key]) {
            positions.value[key].value = data.positions[key].value;
            positions.value[key].timestamp = data.positions[key].timestamp;
          }
        }
      }
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket connection closed');
    updateOpcStatus('Disconnected');
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    updateOpcStatus('Error');
  };
};

// --- Lifecycle Hooks ---
onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
  }
});
</script>

<style scoped>
/* NOTE: The original HTML relied on an external Tailwind script. 
   These styles are a copy of the original <style> block and assume 
   Tailwind utility classes (like flex, grid, etc.) are available 
   in your Vue project's build process. */

.main-container {
  background-color: #ffffff;
  padding: 32px;
  border-radius: 16px; /* More rounded corners */
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15); /* Stronger, but softer shadow */
  text-align: center;
  width: 100%;
  max-width: 1200px; /* Increased max width for more content */
}
.hh1 {
  color: #1a202c; /* Darker text for heading */
  margin-bottom: 24px;
  font-size: 3rem; /* Doubled heading size */
  font-weight: 800; /* Extra bold */
}
/* New styles for OPC Status */
.status-container {
  background-color: #f7fafc;
  border: 1px solid #cbd5e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}
.status-label {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
}
.status-text {
  font-weight: 700;
  font-size: 1.25rem;
  padding: 4px 12px;
  border-radius: 6px;
}
.status-connected {
  color: #2f855a;
  background-color: #c6f6d5;
}
.status-disconnected {
  color: #c53030;
  background-color: #fed7d7;
}
.status-connecting {
  color: #b7791f;
  background-color: #feebc8;
}
.status-error {
  color: #c53030;
  background-color: #fed7d7;
}

/* New group containers for visual separation */
.group-container {
  margin-bottom: 30px;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}
.group-tc {
  background-color: #e0f2fe; /* Light Blue */
}
.group-psra {
  background-color: #e6fffa; /* Light Green */
}
.group-tc2 {
  background-color: #faf5ff; /* Light Purple */
}
.group-psrb {
  background-color: #fefcbf; /* Light Yellow */
}

.machines-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  justify-content: center;
  align-items: stretch;
}
@media (min-width: 640px) {
  .machines-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
.machine-card {
  background-color: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border: 1px solid #e2e8f0;
  height: 100%;
}
.machine-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.12);
}
.machine-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  color: #4299e1;
}
.machine-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 8px;
}
.position-label {
  font-size: 1rem;
  color: #4a5568;
  margin-bottom: 4px;
}
.position-value {
  color: #2563eb;
  font-size: 2.5rem;
  font-weight: 800;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
}
.timestamp-label {
  font-size: 0.875rem;
  color: #718096;
  margin-top: 4px;
}
.line-container {
  width: 100%;
  height: 20px;
  background-color: #cbd5e0;
  border-radius: 10px;
  margin: 20px 0;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}
.machine-marker {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem; /* Reduced font size to fit text */
  font-weight: 600;
  color: #ffffff;
  z-index: 10;
  padding: 10px;
}
.tc-marker {
  background-color: #2563eb;
}
.psr-marker {
  background-color: #8b5cf6;
}
/* Ensure the overall background style from the body is applied to the main container wrapper if needed */
/* Since this is a component, the body styling should be handled by the main app */
</style>