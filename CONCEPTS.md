# Các khái niệm cần biết để hiểu đề tài

**Đề tài:** Cải thiện hiệu năng mạng thông qua việc cộng tác giữa các node mạng nhằm ngăn cản các truy vấn xấu.

File này giải thích từ cơ bản tới các phần dùng trong demo. Đọc theo thứ tự từ trên xuống.

---

## 1. Ý tưởng của đề tài, nói gọn trong 3 câu

1. Kẻ xấu gửi thật nhiều truy vấn rác tới server. Lưu lượng rác chiếm hết đường truyền nên người dùng thật bị chậm hoặc mất kết nối.
2. Nếu chỉ chặn ở **gần server**, rác vẫn đi qua cả mạng và làm nghẽn mọi link trên đường đi.
3. Nếu node gần server **báo cho các node khác** để cùng chặn, thì rác bị chặn ngay **ở cửa vào**, phần mạng bên trong thông thoáng trở lại. Hiệu năng mạng được cải thiện nhờ các node **hợp tác** với nhau.

---

## 2. Khái niệm mạng cơ bản

| Khái niệm | Giải thích ngắn |
|---|---|
| **Node** | Một thiết bị trong mạng: máy tính, router, server... |
| **Link** | Đường nối giữa hai node, có thể là dây thật hoặc dây ảo. |
| **Địa chỉ IP** | "Số nhà" của node, ví dụ `10.0.1.10`. Dạng `10.0.1.0/24` là cả một mạng con gồm 256 địa chỉ từ `10.0.1.0` tới `10.0.1.255`. |
| **Gói tin (packet)** | Đơn vị dữ liệu gửi qua mạng. Mỗi gói ghi rõ IP nguồn (ai gửi) và IP đích (gửi cho ai). |
| **Port (cổng)** | Số dùng để phân biệt các chương trình trên cùng một máy. Server trong demo nghe ở cổng `9000`. |
| **UDP** | Giao thức gửi gói "bắn rồi quên": không bắt tay, không gửi lại khi mất. Gói nhẹ và nhanh, nên rất dễ dùng để flood. Demo dùng UDP. |
| **TCP** | Giao thức có bắt tay, đảm bảo gói tới đủ và đúng thứ tự (web, SSH...). Demo không dùng. |
| **Router** | Node chuyển gói từ mạng này sang mạng khác. Trên Linux, chỉ cần bật `ip_forward` là máy làm được router. |
| **Route (tuyến)** | Quy tắc "muốn tới mạng X thì gửi qua node Y". |
| **Gateway** | Router mặc định: gói nào không biết đi đâu thì gửi cho gateway. |
| **Switch / bridge** | Thiết bị nối nhiều node vào cùng một mạng con. |

---

## 3. Đo hiệu năng mạng

Đây là các chỉ số dùng để chứng minh demo "cải thiện hiệu năng":

| Chỉ số | Ý nghĩa | Khi bị tấn công thì sao |
|---|---|---|
| **Băng thông (bandwidth)** | Lượng dữ liệu tối đa một link truyền được mỗi giây, ví dụ 10 Mbit/s. | Bị rác chiếm hết. |
| **Lưu lượng (throughput)** | Lượng dữ liệu thực tế đang chạy qua link. | Tăng vọt, chạm trần băng thông. |
| **Độ trễ (latency) / RTT** | RTT (Round-Trip Time) là thời gian từ lúc gửi truy vấn tới lúc nhận được trả lời, tính bằng ms. | Tăng mạnh vì gói phải xếp hàng chờ. |
| **Tỉ lệ mất gói (packet loss)** | Phần trăm gói gửi đi nhưng không có trả lời. | Tăng, vì hàng chờ đầy nên gói bị vứt bỏ. |
| **Nút cổ chai (bottleneck)** | Link yếu nhất trên đường đi, quyết định tốc độ của cả tuyến. | Là nơi bị nghẽn đầu tiên. |
| **Hàng đợi (queue)** | Khi gói tới nhanh hơn link kịp truyền, router cho gói xếp hàng chờ. Hàng đợi đầy thì gói mới bị vứt. | Đây là nguyên nhân gây trễ và mất gói. |

**Ví dụ dễ hình dung:** link giống con đường, băng thông là số làn xe, gói tin là xe. Kẻ tấn công cho hàng nghìn xe rác chạy vào đường, xe của người dùng thật phải xếp hàng (trễ) hoặc bị đuổi về (mất gói).

---

## 4. Tấn công và "truy vấn xấu"

| Khái niệm | Giải thích |
|---|---|
| **Truy vấn (query)** | Một yêu cầu gửi tới server và chờ trả lời, ví dụ hỏi DNS hay gọi API. Trong demo, truy vấn là gói UDP `Q <số thứ tự> <thời điểm>`. |
| **Truy vấn xấu** | Truy vấn gửi ra không để dùng, mà để phá: quá nhiều, quá dồn dập, hoặc sai định dạng. Trong demo, "xấu" nghĩa là **một IP gửi quá nhiều truy vấn mỗi giây**. |
| **DoS (Denial of Service)** | Tấn công từ chối dịch vụ: làm server hoặc mạng quá tải để người dùng thật không dùng được. |
| **DDoS** | DoS từ **nhiều** máy cùng lúc (botnet). Demo chỉ mô phỏng **một** máy tấn công cho dễ hiểu. |
| **Flood** | Kiểu tấn công gửi dồn dập thật nhiều gói. Demo dùng **UDP flood**: 5000 gói/s, mỗi gói 1000 byte, tức khoảng 40 Mbit/s, gấp 4 lần băng thông nút cổ chai. |
| **IP giả mạo (spoofing)** | Kẻ tấn công ghi IP nguồn giả vào gói, nên chặn theo IP sẽ khó. Demo **không** xử lý trường hợp này (xem mục 10). |

---

## 5. Phát hiện và chặn

| Khái niệm | Giải thích |
|---|---|
| **Phát hiện dựa trên ngưỡng (threshold)** | Đếm số gói mỗi IP gửi trong 1 giây. Vượt ngưỡng (demo dùng **200 gói/s**) thì coi là tấn công. Client thật chỉ gửi 20 gói/s nên không bị chặn nhầm. |
| **Báo nhầm (false positive)** | Chặn nhầm người dùng thật. Demo tránh bằng hai cách: đặt ngưỡng cách xa lưu lượng thật, và dùng **whitelist** (danh sách không bao giờ chặn: server và client). |
| **Bỏ sót (false negative)** | Không phát hiện được kẻ tấn công, ví dụ kẻ tấn công gửi chậm hơn ngưỡng. |
| **Firewall / iptables** | iptables là tường lửa có sẵn trong Linux. Lệnh `iptables -A GUARD -s 10.0.1.10 -j DROP` có nghĩa là "vứt bỏ mọi gói từ 10.0.1.10". |
| **Chain (chuỗi luật)** | Một nhóm luật của iptables. Chain `FORWARD` áp dụng cho gói **đi xuyên qua** router. Demo tạo chain riêng `GUARD` để thêm và xóa luật cho gọn. |
| **Netfilter** | Phần trong nhân Linux thực thi luật iptables. |

---

## 6. Cộng tác giữa các node: trọng tâm của đề tài

| Khái niệm | Giải thích |
|---|---|
| **Phòng thủ cộng tác (collaborative defense)** | Các node chia sẻ thông tin về kẻ tấn công cho nhau, thay vì mỗi node tự lo. |
| **Cảnh báo (alert)** | Tin nhắn một node gửi cho các node khác. Trong demo có dạng `BLOCK 10.0.1.10 R3`, nghĩa là "R3 báo: hãy chặn 10.0.1.10". |
| **Chặn ở đầu nguồn (upstream / edge filtering)** | Chặn rác ở node **gần kẻ tấn công nhất** (R1). Rác bị vứt sớm nên không tốn băng thông các link phía sau. Đây chính là "cải thiện hiệu năng". |
| **Chặn ở gần nạn nhân** | Chỉ chặn ở R3, cạnh server. Server được bảo vệ, nhưng link R1→R2→R3 vẫn bị rác làm nghẽn. |
| **Mạng điều khiển (control / out-of-band network)** | Mạng riêng `10.0.99.0/24` chỉ dùng để gửi cảnh báo. Vì tách khỏi đường đang bị flood nên cảnh báo luôn tới nơi. Mạng thật cũng hay có mạng quản lý riêng kiểu này. |
| **Data plane / control plane** | Data plane là đường đi của dữ liệu thật (truy vấn). Control plane là đường đi của thông tin điều khiển (cảnh báo). |
| **Gửi cảnh báo chung đường (in-band)** | Cảnh báo không đi mạng riêng mà đi chung đường với dữ liệu R3 → R2 → R1. Giống thực tế hơn, nhưng cần QoS để cảnh báo không bị kẹt sau đống rác. |
| **QoS (Quality of Service)** | Phân loại gói và ưu tiên gói quan trọng, giống xe cứu thương được chen lên đầu hàng khi kẹt xe. Gói được **đánh dấu** bằng một ô trong phần đầu gói IP (DSCP, demo dùng giá trị EF, byte TOS = `0xB8`). Router chia hàng đợi làm 2 làn, gói có dấu đi **làn ưu tiên**, luôn được gửi trước. |
| **Trust boundary** | Ranh giới tin cậy: router ở cửa vào xóa dấu ưu tiên trên gói đến từ bên ngoài, để kẻ tấn công không tự đánh dấu gói rác là ưu tiên. Demo chưa làm bước này. |

**Vì sao node gần server làm nhiệm vụ phát hiện?** Vì node gần nạn nhân thấy rõ nhất ai đang dồn truy vấn vào server. Node ở cửa vào (R1) thì không biết lưu lượng nào là xấu, cho tới khi được báo.

---

## 7. Mô hình demo

```
 Attacker 10.0.1.10 ─┐
                     ├─ R1 ══10Mbit══ R2 ══10Mbit══ R3 ── Server 10.0.3.10
 Client   10.0.1.20 ─┘   │             │              │
                         └──── mạng điều khiển 10.0.99.0/24 ────┘
```

| Lượt | Chuyện gì xảy ra | Kết quả mong đợi |
|---|---|---|
| **off**, không hợp tác | R3 phát hiện và tự chặn. R1, R2 không biết gì. | Server được bảo vệ, nhưng link R1→R2→R3 vẫn đầy rác, client bị **trễ cao**: RTT từ khoảng 0,2 ms tăng lên khoảng 400 ms. |
| **on**, có hợp tác | R3 phát hiện, chặn, rồi **gửi cảnh báo** cho R1, R2 qua mạng điều khiển riêng. R1 chặn ngay ở cửa vào. | Trong 1–2 giây, rác biến mất khỏi mạng, client **trở lại bình thường**. |
| **inband**, có hợp tác | Giống on, nhưng cảnh báo đi **chung đường** R3 → R2 → R1 và được **ưu tiên bằng QoS**. | Giống on: R1 chặn 5 ms sau khi R3 phát hiện. |

**Các chương trình C:**

| Chương trình | Chạy ở | Làm gì |
|---|---|---|
| `server` | Server | Nhận truy vấn, trả lời, in số liệu mỗi giây. |
| `client` | Client | Gửi 20 truy vấn/s, đo RTT và % mất gói, ghi ra file CSV. |
| `attacker` | Attacker | Flood 5000 gói/s. |
| `guard` | R1, R2, R3 | Phát hiện, chặn bằng iptables, gửi và nhận cảnh báo. |

---

## 8. Công cụ và kỹ thuật lập trình

| Khái niệm | Giải thích |
|---|---|
| **Socket** | "Cổng" để chương trình C gửi và nhận dữ liệu qua mạng (`socket()`, `bind()`, `sendto()`, `recvfrom()`). |
| **Raw socket `AF_PACKET`** | Socket đặc biệt cho phép đọc **mọi gói** đi qua một interface, kể cả gói không gửi cho mình. `guard` dùng nó để đếm gói. Cần quyền root. |
| **`poll()`** | Chờ đồng thời nhiều socket, socket nào có dữ liệu thì xử lý socket đó. Nhờ vậy `guard` vừa bắt gói vừa nhận cảnh báo được trong cùng một vòng lặp. |
| **`fork()` + `execvp()`** | Cách `guard` gọi lệnh `iptables` mà không qua shell. An toàn hơn `system()` vì không thể bị chèn lệnh lạ vào. |
| **Signal (SIGINT)** | Tín hiệu gửi khi bấm Ctrl+C. `guard` bắt tín hiệu này để xóa sạch luật iptables trước khi thoát. |
| **Biên dịch tĩnh (`gcc -static`)** | Gói cả thư viện vào file chạy. Biên dịch một lần trên máy bạn là chạy được trên mọi node, không cần cài gcc trong node. |
| **`tc` (traffic control)** | Công cụ Linux để giới hạn băng thông. Lệnh `tc ... tbf rate 10mbit` tạo nút cổ chai 10 Mbit/s. |
| **Network namespace** | Tạo nhiều "máy mạng ảo" ngay trên một máy Linux, mỗi cái có IP, route và iptables riêng. Mini-lab dùng cách này để test nhanh trước khi lên EVE-NG. |
| **veth** | Cặp dây mạng ảo nối hai namespace với nhau. |

---

## 9. Môi trường EVE-NG

| Khái niệm | Giải thích |
|---|---|
| **EVE-NG** | Phần mềm giả lập mạng. Bạn kéo thả các node (router, máy Linux...) rồi nối dây trên giao diện web. Bản Community miễn phí. |
| **Máy ảo (VM)** | Một máy tính giả lập chạy bên trong máy thật. |
| **KVM / QEMU** | Công nghệ máy ảo có sẵn trong Linux. EVE-NG chạy như một máy ảo KVM trên laptop của bạn. |
| **Ảo hóa lồng nhau (nested virtualization)** | Máy ảo chạy bên trong máy ảo: laptop chạy EVE-NG, EVE-NG lại chạy 6 node. Cần CPU hỗ trợ VT-x (máy bạn có). |
| **Image** | File "ổ cứng mẫu" để tạo node. Demo dùng **Alpine Linux** vì rất nhẹ, mỗi node chỉ 256MB RAM. |
| **Management network (Cloud0)** | Mạng nối các node trong EVE-NG ra laptop, để SSH vào điều khiển các node từ script. |
| **SSH** | Đăng nhập và chạy lệnh trên máy khác qua mạng. |

---

## 10. Hạn chế của demo (nên tự nói ra khi trình bày)

Giảng viên thường đánh giá cao khi bạn tự nêu ra hạn chế:

1. **Chưa xác thực cảnh báo.** Kẻ xấu có thể giả cảnh báo để bắt mạng chặn người vô tội. Cách khắc phục: ký cảnh báo bằng HMAC hoặc dùng TLS.
2. **Không chống IP giả mạo.** Kẻ tấn công đổi IP liên tục thì chặn theo IP sẽ không hiệu quả. Cách khắc phục: lọc theo cổng vào (ingress filtering, BCP 38) hoặc phát hiện theo hành vi.
3. **Chỉ có một kẻ tấn công.** DDoS thật đến từ hàng nghìn máy.
4. **Chặn vĩnh viễn.** Chưa có cơ chế tự gỡ chặn sau một thời gian (TTL).
5. **Gửi cảnh báo tới tất cả.** Với mạng lớn cần cơ chế lan truyền thông minh hơn (gossip, gửi theo đường đi của gói).
6. **Mạng điều khiển là một switch chung (lượt on).** Ngoài đời, R1, R2, R3 có thể cách nhau hàng trăm km nên không cắm chung switch được. Lượt **inband** giải quyết điểm này bằng cách cho cảnh báo đi chung đường kèm QoS. Xem câu hỏi ở mục 11.
7. **QoS tin vào dấu ưu tiên trên gói.** Kẻ tấn công tự đánh dấu gói rác là ưu tiên thì sẽ chen được vào làn ưu tiên. Ngoài đời xử lý bằng trust boundary (xem mục 6).

**Các hướng phát triển có thật ngoài thực tế:** Remote Triggered Black Hole (RTBH), BGP FlowSpec (các router của nhà mạng báo nhau chặn lưu lượng tấn công), các dịch vụ chống DDoS như Cloudflare. Chúng dùng đúng ý tưởng của đề tài này ở quy mô Internet.

---

## 11. Câu hỏi giảng viên có thể hỏi và gợi ý trả lời

- **"Sao không chặn luôn ở R1 từ đầu?"** R1 không biết lưu lượng nào là xấu. Chỉ phía server mới thấy ai đang dồn truy vấn vào. Hợp tác giúp đưa thông tin từ nơi *thấy* tới nơi *chặn hiệu quả nhất*.
- **"Cải thiện hiệu năng ở chỗ nào?"** Băng thông link R1→R2→R3 không còn bị rác chiếm, RTT của client giảm từ khoảng 400 ms về khoảng 0,2 ms. Biểu đồ so sánh hai lượt chứng minh điều này.
- **"Sao client bị trễ mà không mất gói?"** Hàng đợi ở nút cổ chai giới hạn theo số byte. Gói rác 1000 byte tới khi hàng đợi gần đầy thì bị vứt, còn gói truy vấn của client rất nhỏ nên vẫn chen vào được, chỉ phải chờ khoảng 400 ms. Với ứng dụng thật như gọi điện hay game, trễ 400 ms đã là không dùng được.
- **"Vì sao giới hạn link xuống 10 Mbit/s?"** Để mô phỏng một nút cổ chai thật. Link ảo trong máy tính quá nhanh nên sẽ không thấy nghẽn.
- **"Cảnh báo bị flood làm mất thì sao?"** Cảnh báo đi trên mạng điều khiển riêng nên không bị ảnh hưởng.
- **"Ngoài đời các router ở xa nhau, làm sao nối chung một switch?"** Đúng là không nối được, switch ở lượt on là để đơn giản hóa. Lượt **inband** cho thấy cách làm không cần switch chung: cảnh báo đi chung đường dữ liệu và được ưu tiên bằng QoS. Ngoài thực tế, kênh cảnh báo có thể là:
  - **Mạng quản lý riêng (out-of-band):** đường truyền riêng chỉ dùng để quản lý thiết bị, tách khỏi đường chở dữ liệu.
  - **VPN:** đi chung Internet nhưng được mã hóa và tách riêng.
  - **Đi chung đường nhưng được ưu tiên (QoS):** gói cảnh báo được chen lên đầu hàng đợi.
  - **BGP FlowSpec:** nhà mạng truyền lệnh chặn từng chặng, từ router này sang router kế bên.

  Ý tưởng của đề tài giữ nguyên: cảnh báo phải đi trên kênh không bị đường đang bị tấn công làm ảnh hưởng.
- **"Làm sao chứng minh QoS có tác dụng?"** Chạy `scripts/qos-check.sh`: cho attacker làm nghẽn đường, rồi đo trên cùng con đường đó. Truy vấn thường mất khoảng 400 ms, truy vấn đánh dấu ưu tiên chỉ khoảng 2 ms. Cảnh báo ở lượt inband được đánh dấu giống hệt.
- **"Sao không dùng luôn QoS để bảo vệ client, khỏi cần chặn?"** Vì dấu ưu tiên chỉ dành cho gói của chính hệ thống (cảnh báo, điều khiển). Nếu ai cũng tự đánh dấu được thì kẻ tấn công cũng làm vậy, và làn ưu tiên lại bị nghẽn. Chặn kẻ tấn công vẫn là cách giải quyết gốc.
- **"R3 có phải là một phần của server không?"** Không. R3 là router riêng đứng ngay trước server, giống router hoặc firewall ở cửa vào mạng của công ty sở hữu server. R1 thường là router của nhà mạng, do bên khác quản lý. Vì vậy R3 không tự cấu hình R1 được mà phải gửi cảnh báo nhờ R1 chặn.
- **"Kẻ xấu giả cảnh báo thì sao?"** Đó là hạn chế số 1. Hướng khắc phục là xác thực cảnh báo.
