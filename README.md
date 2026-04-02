
# Deadline Pool Manager

## Table of Contents

- [Problem](#problem)
- [Pool Manager script](#pool-manager-script)
- [Weighted Snake Draft algorithm](#weighted-snake-draft-algorithm)
    - [Machine power distribution](#machine-power-distribution)
    - [Snake Draft](#snake-draft)
- [Windows Scheduled Task Configuration](#windows-scheduled-task-configuration)
- [Discord Webhook](#discord-webhook)

## Problem

All machines in the farm belong to all pools, which correspond to the current productions at Illogic. Jobs are distributed across the farm based on their pool, priority, and submission time. The order in which pools are assigned to a given machine affects job selection: when multiple jobs with the same priority arrive simultaneously for a CASTOR machine configured with the pools urgent, poolA, and poolB, Deadline processes jobs in the order urgent, then poolA, and finally poolB. While this behavior functions as designed, modifying the pool order for workers in the Deadline interface is not straightforward, as it requires selecting a pool, selecting one or more workers, and using the Promote or Demote actions to adjust their order.

## Pool Manager script

To open the Pool Manager window, click the “**Scripts**” tab at the top left of the window, then hover over “**Illogic**” and click “**Pool Manager**”.

With the Pool Manager, you can use sliders to assign different weights to each pool. These weights determine how many workers are allocated to each pool. For example, a pool with a weight of 20 will receive twice as many workers as a pool with a weight of 10. Therefore, if there are 20 workers in total, the first pool will receive approximately 15 workers and the second 5.

When the window opens, it loads the current weighted pool configuration. You can refresh the slider values by clicking “**Refresh User Data**”. You can also set all sliders to 50 by clicking “**Set Equal Distribution**”. Finally, clicking “**Apply and Save Distribution**” updates the worker pool selection with the selected slider distribution, and saves this configuration to a JSON file for automatic pool updates.

## Weighted Snake Draft algorithm

### Machine power distribution

Since machines have different components and performance characteristics, we assign different profiles to each pool to ensure that the most significant pool does not take all the best machines and likewise that the least significant pools are not disadvantaged.

To ensure an even distribution of machines based on their technical specifications, an evaluation of each machine’s configuration is performed at the time of assignment. Each machine is assigned a score based on the number of CPU cores and the amount of RAM and VRAM.

```python
# Hardware score formula
SCORE** = RAM_GB * 0.5 + CPU_CORES + VRAM_GB * 2
```

The distribution is then performed using a Weighted Snake Draft approach.

### Snake Draft

The snake draft algorithm assigns a worker to each pool, alternating between high-performance and low-performance machines. In the example below, there are 4 pools and 12 workers ranked by performance:

| **Round \ Pool** | **Pool 1** | **Pool 2** | **Pool 3** | **Pool 4** |
| --- | --- | --- | --- | --- |
| **Round 1** | Worker 1 | Worker 2 | Worker 3 | Worker 4 |
| **Round 2** | Worker 12 | Worker 11 | Worker 10 | Worker 9 |
| **Round 3** | Worker 5 | Worker 6 | Worker 7 | Worker 8 |

However, we also take into account the weight of each pool and stop assigning turns to a pool once its threshold has been reached:

```
10 Machines (ranked by power):
🔥🔥🔥 Very-powerful worker x1
🔥🔥    Powerful worker x2
🔥      Mid-range worker x4
💤      Low-performance worker x3

Pool configuration: VCA (weight = 30), Rivers (weight = 15), Sunbrella (weight = 5)

Result:
VCA Pool (6 machines):
🔥🔥🔥 Worker #1
💤      Worker #4
🔥      Worker #6
💤      Worker #8
🔥      Worker #9
🔥      Worker #10

Rivers Pool (3 machines):
🔥🔥    Worker #2
💤      Worker #5
🔥      Worker #7

Sunbrella Pool (1 machine):
🔥🔥    Worker #3
```

> ℹ️ If a given pool has no jobs its weight will dynamically be set to 0 during assignment. This doesn’t affect the saved config.

Finally, we add the remaining pools to the worker pool list in order of weight until every pool has been assigned to every worker. We also place the “urgent” pool at the front of the pool list and the "none" pool at the back.

```
Final pool distribution:
🔥🔥🔥 Worker #1:  urgent, VCA, Rivers, Sunbrella, none
🔥🔥    Worker #2:  urgent, Rivers, VCA, Sunbrella, none
🔥🔥    Worker #3:  urgent, Sunbrella, VCA, Rivers, none
🔥      Worker #4:  urgent, VCA, Rivers, Sunbrella, none
🔥      Worker #5:  urgent, Rivers, VCA, Sunbrella, none
🔥      Worker #6:  urgent, VCA, Rivers, Sunbrella, none
🔥      Worker #7:  urgent, Rivers, VCA, Sunbrella, none
💤      Worker #8:  urgent, VCA, Rivers, Sunbrella, none
💤      Worker #9:  urgent, VCA, Rivers, Sunbrella, none
💤      Worker #10: urgent, VCA, Rivers, Sunbrella, none
```

**TL;DR: The system distributes machines by alternating between high-performance and low-performance workers and rotating across pools, giving more turns to pools with higher weights. This ensures that each pool receives a balanced mix of powerful and less powerful machines, proportional to its needs.**

## Windows Scheduled Task Configuration

**Open the Task Scheduler**

- Press **Win + R**
- Type `taskschd.msc` and press **Enter**

**Create a New Task**

- **Actions** → **Create Task…**

---

**General Tab**

- **Name:** Deadline – Auto Pool Distribution
- **Description:** Automatic redistribution of Deadline pools every 15 minutes
- Check **“Run whether user is logged on or not”**
- Check **“Run with highest privileges”**

---

**Triggers Tab**

- Click **“New…”**
- **Begin the task:** On a schedule
- **Settings:** Daily
- **Repeat task every:** 15 minutes
- **For a duration of:** Indefinitely
- Check **“Enabled”**

---

**Actions Tab**

- Click **“New…”**
- **Action:** Start a program
- **Program/script:**
    
    ```powershell
    ...\PoolManager\run_pool_distribution.bat
    ```
---

**Conditions Tab**

- Uncheck **“Start the task only if the computer is on AC power”**

---

**Settings Tab**

- Check **“Allow task to be run on demand”**
- **If the task is already running:** Do not start a new instance

## Discord Webhook

The **“PoolManagerWebhook.py”** script sends or updates a Discord webhook message with the current pool distribution rates for productions, as defined in a configuration JSON file. It reads the pool distribution data, and formats it into a Discord embed with color-coded bars and emojis based on percentage values. The script keeps track of the last sent message ID to edit the message instead of sending a new one each time. The script is intended to be run using the windows task scheduler with the **“run_pool_webhook.bat”** file.