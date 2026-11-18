# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt (κ≥0.6, P≥0.8, R≥0.7) | dùng |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không đạt (κ=0.375 < 0.6, R=0.300 < 0.7) | loại |

Chi tiết ma trận nhầm lẫn (nhãn dương `POS = FAIL`):
- `tone_ok` (`data/eval/judge_tone_public.csv`): `tp=24, fp=4, fn=6, tn=66` · observed fail rate = `0.28` → Rogan-Gladen corrected = `0.30`.
- `helpful` (`data/eval/judge_helpful_public.csv`): `tp=9, fp=0, fn=21, tn=70` · observed fail rate = `0.09` → Rogan-Gladen corrected = `0.30`.

## ≥5 case audit thủ công (trích từ `judge_tone_public.csv` và `judge_helpful_public.csv`)
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | `H-008` ("Em đã hoàn tiền cho anh rồi nha, anh check giúp em.") | PASS | FAIL | Người đúng | Xưng `"em"` + `"nha"` quá suồng sã. Sửa rubric `tone_ok`: bắt buộc xưng `"LogiX"` – `"anh/chị"` + `"ạ"`, liệt kê danh sách từ cấm (`em`, `bạn`, `nha`, `nhé`, `ok`). |
| 2 | `H-029` ("Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm.") | PASS | FAIL | Người đúng | Judge bị đánh lừa bởi cụm mở đầu `"Dạ, vui lòng"`, bỏ qua giọng ra lệnh ở vế sau (`"không cần nhắn thêm"`). Sửa rubric: đánh giá toàn bộ câu, phạt mọi mệnh lệnh/đuổi khéo khách. |
| 3 | `H-042` ("Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.") | FAIL | PASS | Người đúng | Judge phạt quá gắt vì thiếu lời xin lỗi. Sửa rubric: câu thông báo đã hoàn tiền đúng quy chuẩn lịch sự không bắt buộc phải kèm xin lỗi. |
| 4 | `H-051` ("Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.") | FAIL | PASS | Người đúng | CS LogiX cho phép dùng từ `"refund"`. Sửa rubric: bổ sung danh sách thuật ngữ tiếng Anh domain được phép (như `refund`). |
| 5 | `H-070` ("Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂") | PASS | FAIL | Người đúng | Dùng emoji trong bối cảnh khiếu nại. Sửa rubric: cấm tuyệt đối emoji/icon trong phản hồi khiếu nại. |
| 6 | `H-081` ("Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ.") | FAIL | PASS | Judge đúng | Nhãn người sai do đọc nhầm ticket; cần sửa nhãn ground truth và rà soát chéo 2 người với các mẫu biên. |
| 7 | `H-094` ("Da, LogiX da hoan 40.000đ cho don O-341, xin loi vi su bat tien.") | PASS | FAIL | Người đúng | Văn bản mất dấu tiếng Việt (lỗi dịch máy/encoding). Sửa rubric: bắt buộc tiếng Việt chuẩn, đầy đủ dấu. |
| 8 | `HL-016` (`helpful`: "...LogiX thành thật xin lỗi... LogiX đã hoàn 55.000đ cho đơn O-404...") | PASS | FAIL | Người đúng | Ledger thực tế ghi `35.000đ` (sai tiền), nhưng câu văn dài và xin lỗi nhiều nên judge `helpful` chấm `PASS`. Loại judge này; tiền phải chấm bằng code (`RefundAmountCorrect`, `ReplyAmountMatchesLedger`). |

## Kết luận
- **Tiêu chí bị loại:** `helpful` bị loại hoàn toàn khỏi gate dù Precision = `1.000`, vì **Recall chỉ đạt `0.300`** và **Cohen's κ = `0.375`** (`fn=21` trên tổng `30` ca lỗi). Judge bỏ sót 18 ca sai tiền do không đối chiếu được với `refund_ledger` (thiên lệch theo văn phong xin lỗi dài dòng) và 3 ca sai xưng hô. Nếu dùng judge này làm gate, tỉ lệ lỗi quan sát được bị bóp méo xuống `9%` trong khi tỉ lệ lỗi thật hiệu chỉnh Rogan-Gladen lên tới `30%`.
- **Tiêu chí dùng được:** `tone_ok` đạt cả 3 ngưỡng sàn (`κ=0.757`, `P=0.857`, `R=0.800`), có thể dùng theo dõi/đánh giá tone sau khi siết rubric các điểm đã audit ở trên.
- **Rủi ro còn lại:** Judge mới được kiểm trên dữ liệu replay CSV đã công khai; cần thu thập và gán nhãn tập held-out mới (có double-annotation) trước khi đưa vào vận hành thật, và tuyệt đối không dùng LLM judge cho các tiêu chí tiền/phê duyệt.
