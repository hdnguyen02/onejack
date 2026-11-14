**Title:** Improving network performance through collaborative filtering of malicious queries among network nodes.

**Reason for writing:** A common response to flooding attacks is to filter traffic on the router closest to the victim. That protects the server, but the junk has already crossed every link on the way, so ordinary users on the same path keep suffering. This thesis asks whether a little cooperation between routers can stop that waste.

**Problem:** The router next to the server can tell which source is abusive, but only the edge router can drop that traffic before it uses shared bandwidth. The attack information must travel from one to the other quickly, without blocking legitimate users.

**Methods:** Four C programs were written on Linux: a UDP server, a client that measures round-trip time, an attacker, and a guard for the routers. The guard counts packets per source with a raw socket, blocks any source above {{threshold_en}} packets per second with iptables, and tells the other routers to do the same. A six-node EVE-NG lab with {{bottleneck_en}} Mbit/s bottleneck links was used to compare three runs: blocking only near the server, cooperation over a separate control network, and cooperation over the data path with QoS priority for alerts.

**Results:** Without cooperation, the client's round-trip time stayed around {{rtt_off_en}} ms and the R1–R2 link carried {{link_off_en}} Mbit/s of junk to the end. With cooperation, the edge router blocked the attacker {{block_on_ms_en}} ms after detection, the link dropped to {{link_on_en}} Mbit/s and the round-trip time averaged {{rtt_on_en}} ms. Sending alerts over the data path with QoS gave almost the same result ({{rtt_inband_en}} ms). Under congestion, priority-marked queries took {{qos_prio_eve_en}} ms instead of {{qos_normal_eve_en}} ms.

**Conclusion:** Sharing one block decision between routers restores the network for legitimate users within about a second. Authenticating alerts and handling spoofed or distributed attacks are left as future work.
