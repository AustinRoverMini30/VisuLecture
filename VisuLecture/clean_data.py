import argparse
import copy
import csv
import math

import cv2
import numpy as np
import pandas as pd


POINTS_FILE = "raw.csv"

class Point:
    def __init__(self, timestamp, x, y, jump=False):
        self.timestamp = timestamp
        self.x = x
        self.y = y
        self.jump = jump

def loadPoints(path=None):
    points = []
    with open(f"{path}/{POINTS_FILE}", "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            points.append(Point(float(row[0]), int(row[1]), int(row[2]), False))
    return points

def loadWords(path=None):
    print("path = ", path)
    return pd.read_csv(f"{path}")

def _find_reading_start_index(points, max_skip=40, window_size=10, min_horizontal_ratio=1.5):
    n = len(points)
    if n <= window_size:
        return 0
    last_start = min(max_skip, n - window_size)
    start_idx = 0
    for start in range(last_start + 1):
        p1, p2 = points[start], points[start + window_size - 1]
        dx, dy = p2.x - p1.x, p2.y - p1.y
        if dx > 0 and abs(dx) >= abs(dy) * min_horizontal_ratio:
            start_idx = start
            break
    return start_idx

def _order_box(box):
    box = np.array(box, dtype=np.float32)
    s = box.sum(axis=1)
    d = np.diff(box, axis=1).ravel()
    tl = box[np.argmin(s)]
    br = box[np.argmax(s)]
    tr = box[np.argmin(d)]
    bl = box[np.argmax(d)]
    return np.array([tl, tr, br, bl], dtype=np.float32)

def _recalibrate_points(points, words):
    start_idx = _find_reading_start_index(points)
    pts_reading = np.array([(p.x, p.y) for p in points[start_idx:]], dtype=np.float32)
    rect_reading = cv2.minAreaRect(pts_reading)
    box_reading = cv2.boxPoints(rect_reading)

    pts_words = []
    for _, w in words.iterrows():
        x, y = w["x"], w["y"]
        w_, h_ = w["largeur"], w["hauteur"]
        pts_words.extend([(x, y), (x + w_, y), (x + w_, y + h_), (x, y + h_)])

    pts_words = np.array(pts_words, dtype=np.float32)
    rect_words = cv2.minAreaRect(pts_words)
    box_words = cv2.boxPoints(rect_words)

    src = _order_box(box_reading)
    dst = _order_box(box_words)
    H = cv2.getPerspectiveTransform(src, dst)

    pts_all = np.array([(p.x, p.y) for p in points], dtype=np.float32).reshape(-1, 1, 2)
    pts_corrected_all = cv2.perspectiveTransform(pts_all, H).reshape(-1, 2)

    corrected = []
    for p, (x_new, y_new) in zip(points, pts_corrected_all):
        corrected.append(
            Point(
                timestamp=p.timestamp,
                x=int(round(x_new)),
                y=int(round(y_new)),
                jump=p.jump,
            )
        )
    return corrected

def cleanData(csvPointsPath=None, csvWordsPath=None):
    points = loadPoints(csvPointsPath)
    words = loadWords(csvWordsPath)
    return _recalibrate_points(points, words)

def write_points(points, out_path):
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "x", "y", "jump"])
        for p in points:
            writer.writerow([p.timestamp, p.x, p.y, int(p.jump)])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--points", help="csv points path", default=None)
    parser.add_argument("-w", "--words", help="csv words path", default=None)
    parser.add_argument("-o", "--output", help="output csv path", default="points_cleaned.csv")
    args = parser.parse_args()

    corrected = cleanData(args.points, args.words)  # recalibrage homographie
    words = loadWords(args.words)                   # DataFrame OCR
    line_ys = getLinesList(words)                   # hauteurs de lignes

    corrected = getJumps(corrected, 1920, 1080, nbLines=len(line_ys), lines=line_ys)

    write_points(corrected, args.output)

def getLinesList(words_df):
    return list(words_df.groupby("ligne")["y"].mean().round().astype(int).reset_index()["y"])

def normalize_points_to_lines(points, line_ys):
    if not points:
        return points

    if isinstance(line_ys, pd.DataFrame):
        line_ys = getLinesList(line_ys)
    line_ys = list(line_ys)
    if not line_ys:
        return points

    jump = False
    ligne = 0
    normalized = []

    for p in points:
        if p.jump:
            jump = True
            continue

        if jump and not p.jump:
            ligne += 1
            jump = False
        y = line_ys[min(ligne, len(line_ys)-1)]
        normalized.append(Point(p.timestamp, p.x, y, p.jump))

    return normalized

def isJumpNew(
    currentPoint, nextPoints, coeffCalibration, nbLines,
    averageReadingSpeed, height_coef, width_coef,
    fps=30, width=1920, height=1080
):
    def compute_speeds(pts):
        return [((pts[i].x - pts[i - 1].x)**2 + (pts[i].y - pts[i - 1].y)**2)**0.5 for i in range(1, len(pts))]

    def compute_accelerations(sp):
        return [sp[i] - sp[i - 1] for i in range(1, len(sp))]

    if len(nextPoints) > 1 and average_speed([currentPoint, nextPoints[1]]) < 1000:
        return False, 0

    ##TODO: adapation ici ?     
    authorized_interval_coeff = 1

    for interval_size in range(int(fps / 4), int(fps / 1.5)):
        interval_points = nextPoints[:interval_size]
        if not interval_points:
            continue

        min_x = float("inf")
        index = 0
        gi = 0

        for p in interval_points:
            gi += 1
            if p.x < min_x:
                min_x = p.x
                index = gi

        end_point = len(interval_points)
        for j, point in enumerate(interval_points):
            if point.x > min_x + 5 and j > index:
                end_point = j
                break
        interval_points = interval_points[:end_point]

        if len(interval_points) <= 2:
            continue

        first_point = interval_points[0]
        last_point = interval_points[-1]
        avg_speed = average_speed(interval_points)

        if avg_speed < 1000:
            continue
        if last_point.x >= 0.5 * width:
            continue

        if (
            last_point.x + int(500 * authorized_interval_coeff * width_coef) < first_point.x and
            last_point.y > first_point.y + int(65 * authorized_interval_coeff * height_coef)
        ):
            speeds = compute_speeds(interval_points)
            accels = compute_accelerations(speeds)
            if accels and abs(max(accels) - min(accels)) < averageReadingSpeed * 2:
                return True, interval_size

    return False, 0

def detectJumps(points, width, height, average_speed, width_coeff=1, height_coeff=1):
    result = []
    jump_segments = []

    if len(points) == 1:
        p = points[0]
        result.append(Point(p.timestamp, p.x, p.y, False))
        return result, jump_segments

    n = len(points) 
    i = 0

    while i < n - 1:
        jump, skip = isJumpNew(
            points[i], points[i + 1:], None, None, average_speed, height_coef=height_coeff, width_coef=width_coeff
        )

        result.append(Point(points[i].timestamp, points[i].x, points[i].y, False))

        if not jump:
            i += 1
            continue

        minSkipped = skip
        maxIndex = i + 1

        for index in range(i + 1, i + 1 + skip):
            if index >= len(points):
                break

            jumped, nbSkipped = isJumpNew(
                points[index], points[index:], None, None, average_speed,
                height_coef=height_coeff, width_coef=width_coeff
            )
            if jumped and nbSkipped < minSkipped:
                minSkipped = nbSkipped
                maxIndex = index

        start_idx = maxIndex
        end_idx = min(maxIndex + minSkipped - 1, n - 1)
        jump_segments.append({"start_index": start_idx, "end_index": end_idx})

        for j in range(i + 1, maxIndex):
            if j >= n:
                break
            p = points[j]
            result.append(Point(p.timestamp, p.x, p.y, False))

        for j in range(maxIndex, maxIndex + minSkipped):
            if j >= n:
                break
            p = points[j]
            result.append(Point(p.timestamp, p.x, p.y, True))

        i = maxIndex + minSkipped

    if n > 0:
        last = points[-1]
        result.append(Point(last.timestamp, last.x, last.y, False))

    return result, jump_segments

def getJumps(points, width, height, nbLines, lines, max_iterations=15, fps=30):
    returned_points = []
    avg_reading_speed = average_speed(points)

    adjustedPoints = copy.deepcopy(points)
    width_coeff = 1
    height_coeff = 1

    optimal_number_points_jump = int(fps / 4)
    best_score_optimal_jumps = float("inf")
    index_array_readjusted_jumps = [None] * max_iterations
    array_non_optimal_difference = [None] * max_iterations

    for iteration in range(max_iterations):
        nb_non_optimal_jumps = 0
        optimal = True

        points, jumps = detectJumps(
            adjustedPoints, width, height,
            avg_reading_speed, width_coeff, height_coeff
        )

        if len(jumps) > nbLines - 1:
            height_coeff *= 1.15
        elif len(jumps) < nbLines - 1:
            height_coeff *= 0.85
        else:
            for jump in jumps:
                jump_length = jump["end_index"] - jump["start_index"] + 1

                if jump_length > optimal_number_points_jump + 1:
                    optimal = False

                if jump_length < int(fps / 1.5):
                    start_point = points[jump["start_index"]]
                    before_point = points[jump["start_index"] - 1]

                    if before_point.x - start_point.x > 750 * width_coeff:
                        jump["start_index"] -= 1
                        before_point.jump = True
                        index_array_readjusted_jumps[iteration] = jump["start_index"]

                        if iteration == 0 or index_array_readjusted_jumps[iteration] == index_array_readjusted_jumps[iteration - 1]:
                            optimal = False

                nb_non_optimal_jumps += max(0, jump_length - optimal_number_points_jump)

            array_non_optimal_difference[iteration] = nb_non_optimal_jumps

            if best_score_optimal_jumps > nb_non_optimal_jumps:
                best_score_optimal_jumps = nb_non_optimal_jumps

            returned_points = points

            if optimal:
                break

        if iteration == 0:
            returned_points = points

    return normalize_points_to_lines(returned_points, lines)

def average_speed(nextPoints, fps=30):
    if len(nextPoints) < 2:
        return 0.0

    distances = []
    for i in range(len(nextPoints) - 1):
        p1 = nextPoints[i]
        p2 = nextPoints[i + 1]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        distances.append(dist)

    mean_dist_per_frame = sum(distances) / len(distances)
    mean_speed_per_second = mean_dist_per_frame * fps
    return mean_speed_per_second


if __name__ == "__main__":
    main()
