import argparse
import copy
import csv
import math

import cv2
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

class Point:
    def __init__(self, timestamp, x, y, jump=False, saccade=False):
        self.timestamp = timestamp
        self.x = x
        self.y = y
        self.jump = jump
        self.saccade = saccade

def loadPoints(path=None):
    points = []
    with open(f"{path}", "r") as f:
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
                saccade=getattr(p, 'saccade', False)
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
        writer.writerow(["timestamp", "x", "y", "jump", "saccade"])
        for p in points:
            writer.writerow([p.timestamp, p.x, p.y, int(p.jump), int(getattr(p, 'saccade', False))])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--points", help="csv points path", default=None)
    parser.add_argument("-w", "--words", help="csv words path", default=None)
    parser.add_argument("-o", "--output", help="output csv path", default="points_cleaned.csv")
    args = parser.parse_args()

    corrected = cleanData(args.points, args.words)  # recalibrage homographie
    words = loadWords(args.words)                   # DataFrame OCR
    line_ys = getLinesList(words)                   # hauteurs de lignes
    
    temp = corrected.copy()
    
    for i in range(1000):
        corrected = apply_savitzky_golay(corrected) # lissage des points

    check_back(corrected, temp) # détection des sauts de ligne par recul
    
    limit_back(temp)

    del_small_back(corrected, temp)
    
    speed_back(temp)

    test = normalize_points_to_lines(temp, line_ys)

    #detectSaccades(corrected)

    #corrected = getJumps(corrected, 1920, 1080, nbLines=len(line_ys), lines=line_ys)

    write_points(test, args.output)

def getLinesList(words_df):
    return list(words_df.groupby("ligne")["y"].mean().round().astype(int).reset_index()["y"])

def normalize_points_to_lines(points, line_ys):
    if not points:
        return points
    
    print("line_ys = ", line_ys)

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
        normalized.append(Point(p.timestamp, p.x, y, p.jump, getattr(p, 'saccade', False)))

    return normalized

def isJumpNew(
        currentPoint, nextPoints, coeffCalibration, nbLines,
        averageReadingSpeed, height_coef, width_coef,
        fps=30, width=1920, height=1080
):
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

def compute_speeds(pts):
    return [((pts[i].x - pts[i - 1].x)**2 + (pts[i].y - pts[i - 1].y)**2)**0.5 for i in range(1, len(pts))]

def compute_accelerations(sp):
    return [sp[i] - sp[i - 1] for i in range(1, len(sp))]

def detectJumps(points, width, height, average_speed, width_coeff=1, height_coeff=1):
    result = []
    jump_segments = []

    if len(points) == 1:
        p = points[0]
        result.append(Point(p.timestamp, p.x, p.y, False, getattr(p, 'saccade', False)))
        return result, jump_segments

    n = len(points)
    i = 0

    while i < n - 1:
        jump, skip = isJumpNew(
            points[i], points[i + 1:], None, None, average_speed, height_coef=height_coeff, width_coef=width_coeff
        )

        result.append(Point(points[i].timestamp, points[i].x, points[i].y, False, getattr(points[i], 'saccade', False)))

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
            result.append(Point(p.timestamp, p.x, p.y, False, getattr(p, 'saccade', False)))

        for j in range(maxIndex, maxIndex + minSkipped):
            if j >= n:
                break
            p = points[j]
            result.append(Point(p.timestamp, p.x, p.y, True, getattr(p, 'saccade', False)))

        i = maxIndex + minSkipped

    if n > 0:
        last = points[-1]
        result.append(Point(last.timestamp, last.x, last.y, False, getattr(last, 'saccade', False)))

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

    # Détecter et appliquer les saccades
    detectSaccades(returned_points)

    #return normalize_points_to_lines(returned_points, lines)
    return returned_points

def detectSaccades(points):
    max_speed = 900
    max_accel = 250
    groups = []

    i = 0
    while i + 3 < len(points):
        g = [points[i], points[i + 1], points[i + 2], points[i + 3]]

        if g[0].jump or g[1].jump or g[2].jump or g[3].jump:
            i += 4
            continue

        groups.append(g)
        i += 4

    outliers = []
    for g in groups:
        speeds = compute_speeds(g)            # vitesses
        accels = compute_accelerations(speeds)  # accélérations
        if max(speeds) > max_speed or max(accels) > max_accel:
            g[0].saccade = True
            g[1].saccade = True
            g[2].saccade = True
            g[3].saccade = True
            outliers.append(g)

    return outliers

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

def apply_savitzky_golay(points, window_length=11, polyorder=3):
    """
    Applique le filtre de Savitzky-Golay aux points pour lisser les données.
    
    Args:
        points: Liste de Point à lisser
        window_length: Longueur de la fenêtre (doit être impair et >= polyorder + 2)
        polyorder: Ordre du polynôme pour le filtre
        
    Returns:
        Liste de Point lissés
    """
    if len(points) < window_length:
        # Si pas assez de points, retourner les points originaux
        return points
    
    # Extraire les coordonnées x et y
    x_coords = np.array([p.x for p in points])
    y_coords = np.array([p.y for p in points])
    
    # Appliquer le filtre de Savitzky-Golay
    x_smoothed = savgol_filter(x_coords, window_length, polyorder)
    y_smoothed = savgol_filter(y_coords, window_length, polyorder)
    
    # Créer la liste de points lissés en conservant les autres attributs
    smoothed_points = []
    for i, p in enumerate(points):
        smoothed_points.append(
            Point(
                timestamp=p.timestamp,
                x=int(round(x_smoothed[i])),
                y=int(round(y_smoothed[i])),
                jump=p.jump,
                saccade=getattr(p, 'saccade', False)
            )
        )
    
    return smoothed_points

def check_back(processed_points, original_points):
    """
    Détermine quels points appartiennent à un saut de ligne en se basant sur le recul des points.
    
    Args:
        processed_points: Liste de points traitée (pour détecter les sauts)
        original_points: Liste de points originale (où les propriétés jump seront modifiées)
    """
    if len(processed_points) < 2 or len(processed_points) != len(original_points):
        print("Nombre total de sauts: 0")
        return
    
    jump_count = 0
    
    # Parcourir tous les points pour détecter les reculs
    for i in range(len(processed_points) - 1):
        current_point = processed_points[i]
        next_point = processed_points[i + 1]
        
        # Détecter si le point suivant recule (x2 < x1)
        if next_point.x < current_point.x:
            # Marquer le point suivant comme faisant partie d'un saut
            original_points[i + 1].jump = True
            processed_points[i + 1].jump = True
            jump_count += 1

def limit_back(points):
    """
    Borne les sauts détectés en ne gardant que les points entre le point le plus à droite 
    avant le saut et le point le plus à gauche après le saut.
    
    Args:
        points: Liste de points avec les sauts détectés
    """
    if len(points) < 2:
        return
    
    i = 0
    while i < len(points):
        # Trouver le début d'un groupe de sauts
        if points[i].jump:
            jump_start = i
            jump_end = i
            
            # Trouver la fin du groupe de sauts
            while jump_end < len(points) and points[jump_end].jump:
                jump_end += 1
            
            # jump_end pointe maintenant sur le premier point après le saut (ou fin de liste)
            
            # Trouver le point le plus à droite AVANT le saut
            rightmost_x = float('-inf')
            rightmost_index = jump_start - 1
            
            for j in range(max(0, jump_start - 1), -1, -1):
                if not points[j].jump and points[j].x > rightmost_x:
                    rightmost_x = points[j].x
                    rightmost_index = j
                    break  # On garde le premier point le plus à droite
            
            # Trouver le point le plus à gauche DANS le saut
            leftmost_x = float('inf')
            leftmost_index = jump_end - 1
            
            for j in range(jump_start, jump_end):
                if points[j].x < leftmost_x:
                    leftmost_x = points[j].x
                    leftmost_index = j
            
            # Remettre jump=False pour tous les points AVANT le rightmost
            for j in range(jump_start, min(rightmost_index + 1, jump_end)):
                points[j].jump = False
            
            # Remettre jump=False pour tous les points APRÈS le leftmost
            for j in range(leftmost_index + 1, jump_end):
                points[j].jump = False
            
            # Continuer après ce groupe de sauts
            i = jump_end
        else:
            i += 1

def del_small_back(points, original, min_jump_length=500):
    """
    Supprime les sauts dont la longueur horizontale (xmax - xmin) est inférieure à un seuil.
    
    Args:
        points: Liste de points avec les sauts détectés
        min_jump_length: Longueur minimale d'un saut en pixels (défaut 500)
    """
    if len(points) < 2:
        return
    
    removed_count = 0
    i = 0
    
    while i < len(points):
        if points[i].jump:
            jump_start = i
            jump_end = i
            
            # Trouver la fin du groupe de sauts
            while jump_end < len(points) and points[jump_end].jump:
                jump_end += 1
            
            # Trouver xmin et xmax dans le groupe de sauts
            x_values = [points[j].x for j in range(jump_start, jump_end)]
            x_min = min(x_values)
            x_max = max(x_values)
            
            # Calculer la longueur du saut
            jump_length = x_max - x_min
            
            # Si le saut est trop court, le supprimer
            if jump_length < min_jump_length:
                for j in range(jump_start, jump_end):
                    points[j].jump = False
                    original[j].jump = False
                removed_count += 1
                print(f"Saut rejeté (longueur: {jump_length:.0f} pixels < {min_jump_length})")
            
            i = jump_end
        else:
            i += 1
    
    print(f"Nombre de sauts retirés (trop courts): {removed_count}")

def speed_back(points, fps=30):
    """
    Filtre les faux sauts en comparant leur vitesse avec la vitesse moyenne de lecture.
    Si la vitesse d'un saut est beaucoup plus élevée que la moyenne de lecture (avance),
    il n'est plus considéré comme un saut (jump=False).
    
    Retire aussi les points au début et à la fin des sauts si leur vitesse est dans la moyenne.
    
    Args:
        points: Liste de points avec les sauts détectés
        fps: Frames par seconde (défaut 30)
    """
    if len(points) < 2:
        return
    
    # 1. Calculer la vitesse moyenne de lecture (points sans sauts uniquement)
    reading_points = []
    for i in range(len(points) - 1):
        if not points[i].jump and not points[i + 1].jump:
            reading_points.append(points[i])
    
    if len(reading_points) < 2:
        print("Pas assez de points de lecture pour calculer la vitesse moyenne")
        return
    
    # Ajouter le dernier point si nécessaire
    if not points[-1].jump:
        reading_points.append(points[-1])
    
    # Calculer la vitesse moyenne de lecture (avance)
    avg_reading_speed = average_speed(reading_points, fps)
    
    print(f"Vitesse moyenne de lecture: {avg_reading_speed:.2f} pixels/s")
    
    # Marge de tolérance : un point est considéré "dans la moyenne" 
    # si sa vitesse est entre 0.5x et 2x la vitesse moyenne
    speed_tolerance_min = avg_reading_speed * 0
    speed_tolerance_max = avg_reading_speed * 2.0
    
    # 2. Examiner chaque groupe de sauts
    i = 0
    removed_jumps = 0
    trimmed_points = 0
    
    while i < len(points):
        if points[i].jump:
            jump_start = i
            jump_end = i
            
            # Trouver la fin du groupe de sauts
            while jump_end < len(points) and points[jump_end].jump:
                jump_end += 1
            
            # Extraire les points du saut
            jump_points = points[jump_start:jump_end]
            
            if len(jump_points) < 2:
                i = jump_end
                continue
            
            # Calculer la vitesse du saut
            jump_speed = average_speed(jump_points, fps)
            
            # Logique similaire à isJumpNew: 
            # Un vrai saut de ligne doit avoir une vitesse >= 1000 pixels/s
            # et ne doit pas être beaucoup plus rapide que la vitesse de lecture normale
            
            # Si la vitesse du saut est trop élevée par rapport à la moyenne
            # OU si la vitesse est trop faible (< 1000), ce n'est pas un vrai saut
            if jump_speed < 1000 or jump_speed > avg_reading_speed * 5:
                # Remettre jump=False pour tous les points de ce groupe
                for j in range(jump_start, jump_end):
                    points[j].jump = False
                removed_jumps += 1
                print(f"Saut rejeté (vitesse: {jump_speed:.2f} pixels/s)")
            else:
                # Le saut est valide, mais on doit vérifier les points au début et à la fin
                
                # Retirer les points au DÉBUT du saut s'ils sont dans la moyenne
                new_start = jump_start
                for j in range(jump_start, jump_end - 1):
                    # Calculer la vitesse entre ce point et le suivant
                    if j + 1 < len(points):
                        point_speed = average_speed([points[j], points[j + 1]], fps)
                        if speed_tolerance_min <= point_speed <= speed_tolerance_max:
                            # Ce point a une vitesse normale, on le retire du saut
                            points[j].jump = False
                            new_start = j + 1
                            trimmed_points += 1
                        else:
                            # Dès qu'on trouve un point avec une vitesse de saut, on s'arrête
                            break
                
                # Retirer les points à la FIN du saut s'ils sont dans la moyenne
                new_end = jump_end
                for j in range(jump_end - 1, new_start, -1):
                    # Calculer la vitesse entre ce point et le précédent
                    if j - 1 >= 0:
                        point_speed = average_speed([points[j - 1], points[j]], fps)
                        if speed_tolerance_min <= point_speed <= speed_tolerance_max:
                            # Ce point a une vitesse normale, on le retire du saut
                            points[j].jump = False
                            new_end = j
                            trimmed_points += 1
                        else:
                            # Dès qu'on trouve un point avec une vitesse de saut, on s'arrête
                            break
                
                remaining_jump_points = new_end - new_start
                print(f"Saut conservé (vitesse: {jump_speed:.2f} pixels/s) - {remaining_jump_points} points")
            
            i = jump_end
        else:
            i += 1
    
    print(f"Nombre de sauts retirés: {removed_jumps}")
    print(f"Nombre de points retirés des bords des sauts: {trimmed_points}")

if __name__ == "__main__":
    main()
