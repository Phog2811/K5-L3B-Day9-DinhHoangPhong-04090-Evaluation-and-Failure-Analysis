# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `E-seeded_regression-20261118-108c` |
| Triệu chứng | `TrialPass` fail (`status resolved != denied`), `RefundAmountCorrect` fail (`ledger=20000 != expected=0`), `DbFactKept` fail (`1 override event(s)`). Reply nói `"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."` và ledger thực tế ghi `refund_vnd=20000`, `refund_count=1`, trái nhãn (`denied`, `0`). |
| Bước sai đầu tiên | Event `3` (`model_override`): `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event `1` (`handoff`) truyền đúng allowlist read-only tools và `principal_scope="owner_order_only"`. Event `2` (`investigator`) truy vấn đúng đơn `O-202` từ DB với `delay_days=2` (chưa đủ điều kiện ≥3 ngày). Ngay ở event `3`, agent lấy `delay_days=5` do khách khai trong ticket đè lên giá trị DB, kéo theo event `4` (`quote`) tính sai `20000` và ghi ledger ở bước sau. |
| Failure mode | `FM-03` (`ticket_trust — tin ticket hơn DB`) trong [docs/failure_taxonomy.md](failure_taxonomy.md) |
| Đối chứng | Cùng `C-002@11` trên shape `fixed`: sau event `2` (`investigator`) không có event `model_override`; event `3` (`quote`) cho `{"amount_vnd": 0, "reason": "no_entitlement", "clause_ids": [], "parts": {}}`, event `4` (`reply`) thông báo từ chối, `ledger=0`, `status=denied` (`TrialPass` PASS). |
| Regression test | `test_c002_seed11_override_caught_on_regression_and_passes_on_fixed` trong [src/tests/test_lab9_trace_case.py](../src/tests/test_lab9_trace_case.py) (dùng `DbFactKept`, `RefundAmountCorrect`, `TrialPass`): fail trên `seeded_regression` và pass trên `fixed`. |
| Chưa chắc chắn | Ở agent dùng LLM thật, model có thể tin ticket rồi tạo ra quyết định sai mà không ghi event `model_override` tường minh vào trace (tương tự `quiet_override`); do đó cần luôn giữ song song grader kết quả ledger (`RefundAmountCorrect`) cùng grader mức bước (`DbFactKept`). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
