import cv2
import time

def analyze_video(source=0):
    """
    source:
        0 → webcam
        'path.mp4' → video file
    """

    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("❌ Cannot open video source")
        return

    # 📊 Basic Info
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    print("\n🎥 ===== VIDEO INFO =====")
    print(f"Resolution : {int(width)} x {int(height)}")
    print(f"FPS        : {fps:.2f}")
    print(f"TotalFrames: {int(total_frames)}")

    # Duration
    if fps > 0 and total_frames > 0:
        duration = total_frames / fps
        print(f"Duration   : {duration:.2f} sec")
    else:
        print("Duration   : Not available (Live stream)")

    # Quality
    if width >= 1920:
        print("Quality    : Full HD")
    elif width >= 1280:
        print("Quality    : HD")
    else:
        print("Quality    : Low")

    print("=================================\n")
    print("Press 'q' to exit...\n")

    # 🔥 FPS + Sync variables
    prev_time = time.time()
    frame_time = 1 / fps if fps > 0 else 0.03

    while True:
        start = time.time()

        ret, frame = cap.read()
        if not ret:
            break

        # ⚡ Real FPS
        current_time = time.time()
        real_fps = 1 / (current_time - prev_time)
        prev_time = current_time

        # 🚀 Playback speed
        speed = real_fps / fps if fps > 0 else 1

        # 📊 Display info
        cv2.putText(frame, f"FPS: {int(real_fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"Speed: {speed:.2f}x", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        h, w = frame.shape[:2]
        cv2.putText(frame, f"{w}x{h}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        cv2.imshow("Video Analyzer", frame)

        # 🔥 PERFECT SYNC (MAIN FIX)
        elapsed = time.time() - start
        delay = max(int((frame_time - elapsed) * 1000), 1)

        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# 🔥 RUN HERE
if __name__ == "__main__":
    # Webcam
    # analyze_video(0)

    # Video file
    analyze_video("C:/ROI_SAS/TESTING_INPUT.mp4")