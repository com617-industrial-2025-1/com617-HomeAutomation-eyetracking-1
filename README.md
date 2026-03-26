# Node-RED Velbus Control
---

## Prerequisites

* [Node-RED](https://nodered.org/)
* [velserv](https://github.com/jeroends/velserv)
* Raspberry Pi

---

## Installation & Setup
### 1. Install Node-RED onto the Raspberry Pi
To run Node-RED on the Raspberry Pi follow [this](https://nodered.org/docs/getting-started/raspberrypi) offical guide.
### 2. Install Node-RED Velbus Plugin
To interact with the Velbus protocol, you need the dedicated palette nodes:

1. Open your Node-RED editor (usually `http://localhost:1880`).
2. Click the **Menu** (top right) > **Manage palette**.
3. Go to the **Install** tab and search for:
   `node-red-contrib-velbus`
4. Click **Install**.

### 2. Configure the USB-to-TCP Bridge
Node-RED communicates with the Velbus hardware via a socket. Since the hardware uses USB serial, you must use a TCP server to bridge the communication.

**Recommendation:** [velserv](https://github.com/jeroends/velserv) by jeroends

**Setup:** Follow the instructions on the velserv GitHub to compile and run it on your host machine.

## 3. Implementation

### Option A: Import an Existing Flow
If you are using a pre-made flow from this repository:
1. Copy the JSON content from the `flows.json` file.
2. In Node-RED, go to **Menu** > **Import**.
3. Paste the JSON and click **Import to workspace**.

### Option B: Create Your Own Flow
To control a relay by **Send Raw Bytes** node:
* **Select Velbus Port:** Configure a **TCP Request** node with the IP and Port (default `127.0.0.1:6000`) of your `velserv` host.
* **Select Relay Address:** In a **Function** node through msg or directly in the **Send Raw Bytes** node, define the destination address of your relay module.
* **Define Data Bytes:** Send a Buffer containing the raw Velbus hex string, create your own string or choose one form the dropdown.
  
  * For more advanced setups, specialized nodes for **Dimmers**, **Temperature** or **Buttons** can be used insead of the **Send Raw Bytes** node.
---
