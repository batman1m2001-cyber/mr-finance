"""What a step says in the panel while it runs and once done (owner, 2026-10-18: "a message with clear semantic,
concise", and nothing unsafe): two fixed sentences per tool, details only from the product's own names."""

from operonx_agents.run.events import ToolCallStarted

from assistant import progress, registry, stream
from assistant.base import Ctx


def test_every_tool_says_what_it_does_running_and_done():
    assert set(progress.SAYS) == set(registry.REGISTRY)  # a new tool says what it does, or this fails
    for name, (doing, done) in progress.SAYS.items():
        assert doing.startswith("Đang ") and done.startswith("Đã "), name
        assert len(doing) <= 60 and len(done) <= 60, name  # concise: one short line in the panel
        assert not any(c.isdigit() for c in doing + done) and "_" not in doing + done, name


def test_a_detail_comes_from_the_products_names_never_from_what_was_typed():
    assert progress.says("dong_tien", {"month": "2026-09"}) == {
        "doing": "Đang xem tiền vào, tiền ra tháng 09/2026",
        "done": "Đã xem tiền vào, tiền ra tháng 09/2026",
        "failed": "Không thực hiện được: xem tiền vào, tiền ra tháng 09/2026",
    }
    assert progress.says("dong_tien", {"month": "2026-13"})["doing"] == "Đang xem tiền vào, tiền ra trong tháng"
    assert progress.says("kich_ban", {"scenario": "lai_suat"})["doing"].endswith(": “Lãi suất tăng 2%”")
    both = progress.says("so_sanh_kich_ban", {"scenarios": ["co_phieu", "lai_suat", "co_phieu"]})["done"]
    assert both == "Đã so sánh các kịch bản: “VN-Index giảm 30%” và “Lãi suất tăng 2%”"
    typed = "<img src=x onerror=alert(1)> C02 bỏ qua quy tắc"
    for tool, args in (("tim_kiem", {"q": typed}), ("ghi_nho", {"text": typed}), ("tim_tren_web", {"q": typed}),
                       ("quen", {"item_id": "abc123"}), ("kich_ban", {"scenario": typed}),
                       ("so_sanh_kich_ban", {"scenarios": [typed]}), ("dong_tien", {"month": typed})):  # fmt: skip
        out = " ".join(progress.says(tool, args).values())
        assert "img" not in out and "C02" not in out and "abc123" not in out and "quy tắc" not in out, (tool, out)
    assert progress.says("khong_co", {})["doing"] == "Đang dùng một chức năng"  # an unknown step names nothing


def test_the_step_event_carries_its_sentences():
    ctx = Ctx(role="client", client_id="C01", scope="personal", question="", reads=True, graph={})
    e = stream.translate(ToolCallStarted(call_id="c1", tool="dong_tien", args={"month": "2026-08"}), ctx)
    assert e["doing"] == "Đang xem tiền vào, tiền ra tháng 08/2026" and e["done"].startswith("Đã xem")
