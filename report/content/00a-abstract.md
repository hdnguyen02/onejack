**Title:** Improving network performance: reducing latency through path selection and load distribution across routers.

**Reason for writing:** Interactive services such as voice calls, video meetings and online games need data to arrive quickly. When heavy traffic shares the same links, packets wait in router queues and latency grows to hundreds of milliseconds. Networks often have more than one path between two points, but routers may send everything over a single path.

**Problem:** With the same links and devices, how should routers choose paths so that users see the lowest latency, both when the network is idle and when it is loaded?

**Methods:** A six-node network was built in EVE-NG with Linux routers and two paths between the edge routers: a long path through an intermediate router and a short direct path. Each router link was emulated with {{link_delay_en}} ms of propagation delay and {{link_rate_en}} Mbit/s of bandwidth using tc. Three C programs were written: a server, a client that measures round-trip time, jitter and loss, and a load generator that sends {{load_mbit_en}} Mbit/s in {{load_flows_en}} flows. Three routing setups were compared: all traffic on the long path, all traffic on the short path, and equal-cost multipath routing that spreads flows over both paths.

**Results:** With no load, the short path lowered the client's round-trip time from {{idle_base_en}} ms to {{idle_short_en}} ms. Under load, a single path was congested and the round-trip time rose to {{rtt_base_en}} ms on the long path and {{rtt_short_en}} ms on the short path. Spreading the load over both paths kept it at {{rtt_balance_en}} ms, a {{rtt_drop_balance_en}}% reduction, and the server received the full {{server_balance_en}} Mbit/s instead of {{server_base_en}} Mbit/s.

**Conclusion:** A shorter path reduces latency only while the network is idle, because queueing delay dominates under load. Distributing load over the available paths removes most of that queueing delay. Both changes need only routing table updates, with no new hardware or extra bandwidth.
