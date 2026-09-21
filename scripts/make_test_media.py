"""Small deterministic browser fixtures, restricted to the repository E2E directory."""

import io
import os
from pathlib import Path

import av
from PIL import Image, ImageDraw


def main():
    parent = Path(__file__).resolve().parents[1] / ".workspace" / "e2e"
    run = Path(os.environ.get("AVW_E2E_RUN_DIRECTORY", parent)).resolve()
    if not run.is_relative_to(parent.resolve()):
        raise ValueError("Fixtures must stay inside the E2E directory")
    root = run / "fixtures"
    root.mkdir(parents=True, exist_ok=True)
    for name, color in (("reference", "#53d9b0"), ("scene", "#e5ba72"), ("storyboard", "#aebbc3")):
        image = Image.new("RGB", (640, 360), "#191f23")
        draw = ImageDraw.Draw(image)
        for row in range(2):
            for col in range(3):
                x, y = 20 + col * 208, 20 + row * 168
                draw.rounded_rectangle((x, y, x + 188, y + 148), radius=10, outline=color, width=3)
                draw.text((x + 15, y + 15), f"SPF TEST / {row * 3 + col + 1:02}", fill=color)
                draw.line((x + 35, y + 115, x + 95, y + 55, x + 155, y + 115), fill=color, width=3)
        image.save(root / f"{name}.png")
    output = io.BytesIO()
    with av.open(output, "w", format="mp4") as container:
        stream = container.add_stream("libx264", rate=24)
        stream.width, stream.height, stream.pix_fmt = 160, 90, "yuv420p"
        stream.thread_count = 1
        for i in range(24):
            frame = av.VideoFrame.from_image(Image.new("RGB", (160, 90), (30, 90 + i, 75)))
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    (root / "video.mp4").write_bytes(output.getvalue())


if __name__ == "__main__":
    main()
