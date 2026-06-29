"""
Pazaak: The Kobayashi Maru of Star Wars

Script: click_coords.py
Author: Sebastian Böker

Utility script used during calibration of the extraction pipeline.

The script loads the first PNG image found in the screenshots folder
and displays it in an OpenCV window. Left-clicking anywhere on the
image prints the corresponding pixel coordinates to the terminal.

This tool was primarily used to determine fixed board locations for:

    - player card slots
    - opponent card slots
    - template matching regions

Controls:
    Left Mouse Button  -> print coordinates
    ESC                -> close window
"""

from pathlib import Path
import cv2


BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"


def on_mouse(event, x, y, flags, param):
    """Print pixel coordinates when the left mouse button is pressed."""
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"({x}, {y})")


def main() -> None:
    """Load a screenshot and allow interactive coordinate inspection."""
    screenshots = sorted(SCREENSHOT_DIR.glob("*.png"))

    if not screenshots:
        raise FileNotFoundError(
            f"No PNG files found in {SCREENSHOT_DIR}"
        )

    screenshot = screenshots[0]
    img = cv2.imread(str(screenshot))

    if img is None:
        raise FileNotFoundError(screenshot)

    print(f"Loaded: {screenshot.name}")
    print("Left-click to print coordinates. Press ESC to exit.")

    window_name = "click_coords"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, img)
    cv2.setMouseCallback(window_name, on_mouse)

    while True:
        key = cv2.waitKey(20)

        if key == 27:  # ESC
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()